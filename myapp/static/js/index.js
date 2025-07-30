// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 100) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
        navbar.style.boxShadow = '0 2px 30px rgba(0, 0, 0, 0.15)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
    }
});

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', () => {
    // Set initial styles for animation
    const animateElements = document.querySelectorAll('.feature-card, .stat, .tech-item');
    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // Counter animation for stats
    const stats = document.querySelectorAll('.stat h3');
    const isNumberStat = (text) => /^\d+/.test(text);
    
    const animateCounter = (element, target) => {
        let current = 0;
        const increment = target / 100;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current) + (target === 99 ? '%' : '');
        }, 20);
    };

    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const text = entry.target.textContent;
                if (text.includes('99%')) {
                    animateCounter(entry.target, 99);
                }
                statsObserver.unobserve(entry.target);
            }
        });
    });

    stats.forEach(stat => {
        if (stat.textContent.includes('99%')) {
            statsObserver.observe(stat);
        }
    });

    // Parallax effect for hero image
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const heroImage = document.querySelector('.hero-image img');
        if (heroImage && scrolled < window.innerHeight) {
            heroImage.style.transform = `translateY(${scrolled * 0.3}px)`;
        }
    });

    // Hover effects for feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(-5px) scale(1)';
        });
    });
});

// Loading animation
window.addEventListener('load', () => {
    document.body.style.opacity = '1';
});

// Set initial body opacity for smooth load
document.body.style.opacity = '0';
document.body.style.transition = 'opacity 0.5s ease';

// Hidden admin access - click on brand logo 5 times
let clickCount = 0;
const requiredClicks = 5;
const resetTime = 3000; // 3 seconds

document.addEventListener('DOMContentLoaded', () => {
    const navBrand = document.querySelector('.nav-brand');
    const adminAccess = document.getElementById('admin-access');
    let resetTimer;

    navBrand.addEventListener('click', (e) => {
        clickCount++;
        
        // Visual feedback for clicks
        navBrand.style.transform = 'scale(0.95)';
        setTimeout(() => {
            navBrand.style.transform = 'scale(1)';
        }, 100);
        
        // Reset timer
        clearTimeout(resetTimer);
        resetTimer = setTimeout(() => {
            clickCount = 0;
        }, resetTime);

        // Show admin access after required clicks
        if (clickCount >= requiredClicks) {
            adminAccess.style.display = 'block';
            adminAccess.style.animation = 'fadeIn 0.5s ease';
            
            // Add CSS for fade in animation
            if (!document.querySelector('#fadeInStyle')) {
                const style = document.createElement('style');
                style.id = 'fadeInStyle';
                style.textContent = `
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(10px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                `;
                document.head.appendChild(style);
            }
            
            // Auto navigate to login page after showing access
            setTimeout(() => {
                window.location.href = '/login/';
            }, 500);
            
            clickCount = 0;
            clearTimeout(resetTimer);
        }
    });

    // Add cursor pointer to nav brand and smooth transition
    navBrand.style.cursor = 'pointer';
    navBrand.style.transition = 'transform 0.1s ease';
});
