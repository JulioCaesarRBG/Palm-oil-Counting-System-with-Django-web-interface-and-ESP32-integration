from django.shortcuts import render, redirect
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from datetime import datetime, timedelta, date
from .models import PalmOilCount
from django.db.models import Sum
from django.db.models.functions import TruncWeek
from ultralytics import YOLO
import cv2
import threading
from .detection_state import detection_state
import os
import requests
from django.conf import settings
from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

# Buat fungsi helper untuk mendapatkan URL server deteksi
def get_detection_server_url():
    config = settings.DETECTION_SERVER_CONFIG
    base_url = f"{config['HOST']}:{config['PORT']}"
    
    # Jika berjalan di mesin yang sama, coba localhost dulu
    if config['HOST'] in ['http://192.168.137.150', 'http://127.0.0.1', 'http://localhost']:
        # Coba localhost terlebih dahulu
        try:
            import requests
            test_url = f"http://localhost:{config['PORT']}/get_counts"
            response = requests.get(test_url, timeout=2)
            if response.status_code == 200:
                return f"http://localhost:{config['PORT']}"
        except:
            pass
        
        # Jika localhost gagal, coba IP yang dikonfigurasi
        try:
            test_url = f"{base_url}/get_counts"
            response = requests.get(test_url, timeout=2)
            if response.status_code == 200:
                return base_url
        except:
            pass
    
    return base_url

def index(request):
    import time
    timestamp = int(time.time())  # Current timestamp to force cache refresh
    return render(request, 'myapp/index.html', {'timestamp': timestamp})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('myapp:dashboard')
        else:
            messages.error(request, 'Username atau password salah!')
    return render(request, 'myapp/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('myapp:index')

@login_required
def dashboard(request):
    # Dapatkan tanggal hari ini
    today = timezone.now()
    
    # Hitung awal dan akhir minggu (Senin-Minggu)
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_of_week = start_of_week + timedelta(days=6)
    end_of_week = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Ambil data untuk minggu ini
    weekly_data = PalmOilCount.objects.filter(
        date__range=[start_of_week, end_of_week]
    ).aggregate(
        weekly_suitable=Sum('suitable_count'),
        weekly_unsuitable=Sum('unsuitable_count')
    )

    # Siapkan data harian untuk chart
    daily_data = []
    for i in range(7):  # 7 hari dalam seminggu
        current_date = start_of_week + timedelta(days=i)
        next_date = current_date + timedelta(days=1)
        
        daily_counts = PalmOilCount.objects.filter(
            date__range=[current_date, next_date]
        ).aggregate(
            suitable_count=Sum('suitable_count'),
            unsuitable_count=Sum('unsuitable_count')
        )
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day': current_date.strftime('%a'),  # Nama hari singkat (Mon, Tue, etc.)
            'suitable_count': daily_counts['suitable_count'] or 0,
            'unsuitable_count': daily_counts['unsuitable_count'] or 0
        })

    # Data terakhir untuk status
    latest_count = PalmOilCount.objects.order_by('-date').first()

    context = {
        'weekly_suitable': weekly_data['weekly_suitable'] or 0,
        'weekly_unsuitable': weekly_data['weekly_unsuitable'] or 0,
        'last_counted': latest_count.date if latest_count else None,
        'start_of_week': start_of_week.strftime('%d %B %Y'),
        'end_of_week': end_of_week.strftime('%d %B %Y'),
        'chart_data': json.dumps(daily_data),  # Serialize ke JSON string
        'counting_status': latest_count.status if latest_count else 'stopped'
    }
    
    return render(request, 'myapp/dashboard.html', context)

@login_required
def control(request):
    latest_data = PalmOilCount.objects.first()
    context = {
        'latest_count': {
            'suitable_count': latest_data.suitable_count if latest_data else 0,
            'unsuitable_count': latest_data.unsuitable_count if latest_data else 0,
            'image': latest_data.image if latest_data else None
        }
    }
    return render(request, 'myapp/control.html', context)

@login_required
def tables(request):
    table_data = PalmOilCount.objects.all().order_by('-date')
    
    # Format data untuk template dengan tanggal yang konsisten
    formatted_data = []
    for item in table_data:
        formatted_item = {
            'id': item.id,
            'date': item.date.strftime('%Y-%m-%d'),  # Format YYYY-MM-DD untuk filter
            'date_display': item.date.strftime('%d/%m/%Y'),  # Format display yang user-friendly
            'suitable_count': item.suitable_count,
            'unsuitable_count': item.unsuitable_count,
            'image': item.image if item.image else None,
            'status': item.status
        }
        formatted_data.append(formatted_item)
        
        # Debug logging
        print(f"Item {item.id}: date={formatted_item['date']}, display={formatted_item['date_display']}")
        
        if item.image:
            print(f"Image path: {item.image.path}")
            print(f"Image URL: {item.image.url}")
    
    print(f"Total items sent to template: {len(formatted_data)}")
    return render(request, 'myapp/tables.html', {'table_data': formatted_data})

@login_required
def start_detection(request):
    try:
        # Pastikan tidak ada sesi yang sedang berjalan
        active_session = PalmOilCount.objects.filter(status__in=['running', 'paused']).first()
        if active_session:
            active_session.status = 'stopped'
            active_session.save()

        response = requests.post(
            f"{get_detection_server_url()}/start",
            timeout=settings.DETECTION_SERVER_CONFIG['TIMEOUT']
        )
        
        # Hapus pembuatan record baru di sini karena akan dibuat oleh detection server
        return JsonResponse(response.json())
    except requests.exceptions.ConnectionError as e:
        return JsonResponse({
            "status": "error",
            "message": f"Cannot connect to detection server. Please check:\n1. Detection server is running\n2. IP address is correct: {get_detection_server_url()}\n3. Firewall allows port 5000\n\nError: {str(e)}"
        })
    except requests.exceptions.Timeout as e:
        return JsonResponse({
            "status": "error", 
            "message": f"Connection to detection server timed out. Server may be overloaded or network is slow. Error: {str(e)}"
        })
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"Cannot connect to detection server: {str(e)}"
        })

@login_required
def pause_detection(request):
    try:
        response = requests.post(
            f"{get_detection_server_url()}/pause",
            timeout=settings.DETECTION_SERVER_CONFIG['TIMEOUT']
        )
        
        if response.json()['status'] == 'paused':
            # Update status sesi yang sedang berjalan
            current_session = PalmOilCount.objects.filter(status='running').first()
            if current_session:
                current_session.status = 'paused'
                current_session.save()
        
        return JsonResponse(response.json())
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"Cannot connect to detection server: {str(e)}"
        })

@login_required
def resume_detection(request):
    try:
        response = requests.post(
            f"{get_detection_server_url()}/resume",
            timeout=settings.DETECTION_SERVER_CONFIG['TIMEOUT']
        )
        
        if response.json()['status'] == 'resumed':
            # Update status sesi yang sedang berjalan
            current_session = PalmOilCount.objects.filter(status='paused').first()
            if current_session:
                current_session.status = 'running'
                current_session.save()
        
        return JsonResponse(response.json())
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"Cannot connect to detection server: {str(e)}"
        })

@login_required
def stop_detection(request):
    try:
        response = requests.post(
            f"{get_detection_server_url()}/stop",
            timeout=settings.DETECTION_SERVER_CONFIG['TIMEOUT']
        )
        
        # Hapus update status di sini karena sudah ditangani oleh detection server
        return JsonResponse(response.json())
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"Cannot connect to detection server: {str(e)}"
        })

def gen_frames():
    while True:
        if detection_state.cap and detection_state.is_running:
            ret, frame = detection_state.cap.read()
            if not ret:
                break
            
            # Gunakan frame yang sudah diproses jika ada
            if hasattr(detection_state, 'current_frame') and detection_state.current_frame is not None:
                frame = detection_state.current_frame
                
            # Encode frame ke format JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@login_required
def video_feed(request):
    try:
        return StreamingHttpResponse(
            requests.get(
                f"{get_detection_server_url()}/video_feed",
                stream=True,
                timeout=settings.DETECTION_SERVER_CONFIG['TIMEOUT']
            ),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"Cannot connect to video feed: {str(e)}"
        })

@login_required
def get_counts(request):
    try:
        response = requests.get(
            f"{get_detection_server_url()}/get_counts",
            timeout=settings.DETECTION_SERVER_CONFIG['TIMEOUT']
        )
        data = response.json()
        
        # Hapus pembuatan/update record di sini karena sudah ditangani oleh detection server
        return JsonResponse(data)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"Cannot connect to detection server: {str(e)}"
        })

@login_required
def get_week_data(request):
    """
    API endpoint untuk mendapatkan data dashboard berdasarkan minggu tertentu
    """
    try:
        # Ambil parameter week dari request
        week_str = request.GET.get('week')
        if not week_str:
            return JsonResponse({
                "status": "error",
                "message": "Week parameter is required"
            }, status=400)
        
        # Parse week string (format: "YYYY-MM-DD")
        try:
            week_date = datetime.strptime(week_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid week date format. Use YYYY-MM-DD"
            }, status=400)
        
        # Hitung start dan end date untuk minggu tersebut
        # Asumsi minggu dimulai hari Senin
        days_since_monday = week_date.weekday()
        week_start = week_date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        # Ambil data untuk minggu tersebut
        week_data = PalmOilCount.objects.filter(
            created_at__date__range=[week_start, week_end]
        ).values(
            'created_at__date'
        ).annotate(
            suitable_count=Sum('suitable_count'),
            unsuitable_count=Sum('unsuitable_count')
        ).order_by('created_at__date')
        
        # Format data untuk chart
        daily_data = []
        for i in range(7):  # 7 hari dalam seminggu
            current_date = week_start + timedelta(days=i)
            day_name = current_date.strftime('%A')  # Monday, Tuesday, etc.
            
            # Cari data untuk hari ini
            day_data = next(
                (item for item in week_data if item['created_at__date'] == current_date),
                {'suitable_count': 0, 'unsuitable_count': 0}
            )
            
            daily_data.append({
                'day': day_name,
                'date': current_date.strftime('%Y-%m-%d'),
                'suitable_count': day_data['suitable_count'] or 0,
                'unsuitable_count': day_data['unsuitable_count'] or 0
            })
        
        # Hitung total untuk minggu ini
        total_suitable = sum(day['suitable_count'] for day in daily_data)
        total_unsuitable = sum(day['unsuitable_count'] for day in daily_data)
        total_count = total_suitable + total_unsuitable
        
        return JsonResponse({
            "status": "success",
            "data": {
                "week_start": week_start.strftime('%Y-%m-%d'),
                "week_end": week_end.strftime('%Y-%m-%d'),
                "daily_data": daily_data,
                "totals": {
                    "suitable_count": total_suitable,
                    "unsuitable_count": total_unsuitable,
                    "total_count": total_count
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Error retrieving week data: {str(e)}"
        }, status=500)

@csrf_exempt
def save_count_data_api(request):
    """
    API endpoint untuk menerima data dari detection server
    """
    if request.method == 'POST':
        try:
            # Cek apakah ada file upload
            if request.content_type and 'multipart/form-data' in request.content_type:
                # Request dengan file
                suitable_count = int(request.POST.get('suitable_count', 0))
                unsuitable_count = int(request.POST.get('unsuitable_count', 0))
                status = request.POST.get('status', 'running')
                image = request.FILES.get('image', None)
            else:
                # Request JSON biasa
                data = json.loads(request.body)
                suitable_count = data.get('suitable_count', 0)
                unsuitable_count = data.get('unsuitable_count', 0)
                status = data.get('status', 'running')
                image = None
            
            # Buat record baru di database
            count_record = PalmOilCount.objects.create(
                suitable_count=suitable_count,
                unsuitable_count=unsuitable_count,
                status=status,
                date=timezone.now(),
                image=image  # Simpan gambar jika ada
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Data saved successfully",
                "id": count_record.id,
                "data": {
                    "suitable_count": count_record.suitable_count,
                    "unsuitable_count": count_record.unsuitable_count,
                    "status": count_record.status,
                    "date": count_record.date.isoformat(),
                    "image": count_record.image.url if count_record.image else None
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON data"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error saving data: {str(e)}"
            }, status=500)
    else:
        return JsonResponse({
            "status": "error",
            "message": "Only POST method allowed"
        }, status=405)

@csrf_exempt
def update_count_data_api(request, record_id):
    """
    API endpoint untuk update data yang sudah ada dari detection server
    """
    if request.method == 'PUT':
        try:
            # Parse JSON data
            data = json.loads(request.body)
            suitable_count = data.get('suitable_count', 0)
            unsuitable_count = data.get('unsuitable_count', 0)
            status = data.get('status', 'running')
            
            # Update record yang sudah ada
            try:
                count_record = PalmOilCount.objects.get(id=record_id)
                count_record.suitable_count = suitable_count
                count_record.unsuitable_count = unsuitable_count
                count_record.status = status
                count_record.save()
                
                return JsonResponse({
                    "status": "success",
                    "message": "Data updated successfully",
                    "id": count_record.id,
                    "data": {
                        "suitable_count": count_record.suitable_count,
                        "unsuitable_count": count_record.unsuitable_count,
                        "status": count_record.status,
                        "date": count_record.date.isoformat()
                    }
                })
                
            except PalmOilCount.DoesNotExist:
                return JsonResponse({
                    "status": "error",
                    "message": "Record not found"
                }, status=404)
            
        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON data"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error updating data: {str(e)}"
            }, status=500)
    else:
        return JsonResponse({
            "status": "error",
            "message": "Only PUT method allowed"
        }, status=405)
