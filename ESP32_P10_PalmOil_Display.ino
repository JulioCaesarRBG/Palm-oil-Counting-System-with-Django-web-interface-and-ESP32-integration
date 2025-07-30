//>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ESP32_P10_PalmOil_Display
//----------------------------------------Including the libraries.
#include <DMD32.h>  //--> DMD32 by Qudor-Engineer (KHUDHUR ALFARHAN) : https://github.com/Qudor-Engineer/DMD32
#include "fonts/SystemFont5x7.h"
#include "fonts/Arial_black_16.h"
//----------------------------------------

// Fire up the DMD library as dmd.
#define DISPLAYS_ACROSS 3
#define DISPLAYS_DOWN 1
DMD dmd(DISPLAYS_ACROSS, DISPLAYS_DOWN);

// Timer setup.
// create a hardware timer  of ESP32.
hw_timer_t * timer = NULL;

// Variables for palm oil counts
int ripeCount = 0;
int unripeCount = 0;
String detectionStatus = "stopped";
unsigned long lastUpdate = 0;
const unsigned long updateInterval = 1000; // Update every 1 second

//________________________________________________________________________________IRAM_ATTR triggerScan()
//  Interrupt handler for Timer1 (TimerOne) driven DMD refresh scanning,
//  this gets called at the period set in Timer1.initialize();
void IRAM_ATTR triggerScan() {
  dmd.scanDisplayBySPI();
}
//________________________________________________________________________________

//________________________________________________________________________________parseSerialData()
void parseSerialData(String data) {
  // Expected format: "RIPE:5,UNRIPE:3,STATUS:running"
  int ripeIndex = data.indexOf("RIPE:");
  int unripeIndex = data.indexOf("UNRIPE:");
  int statusIndex = data.indexOf("STATUS:");
  
  if (ripeIndex != -1) {
    int commaIndex = data.indexOf(",", ripeIndex);
    if (commaIndex != -1) {
      ripeCount = data.substring(ripeIndex + 5, commaIndex).toInt();
    }
  }
  
  if (unripeIndex != -1) {
    int commaIndex = data.indexOf(",", unripeIndex);
    if (commaIndex != -1) {
      unripeCount = data.substring(unripeIndex + 7, commaIndex).toInt();
    } else {
      // If this is the last parameter without comma
      int statusPos = data.indexOf(",STATUS:");
      if (statusPos != -1) {
        unripeCount = data.substring(unripeIndex + 7, statusPos).toInt();
      }
    }
  }
  
  if (statusIndex != -1) {
    detectionStatus = data.substring(statusIndex + 7);
    detectionStatus.trim(); // Remove any whitespace
  }
  
  Serial.println("Parsed - Ripe: " + String(ripeCount) + ", Unripe: " + String(unripeCount) + ", Status: " + detectionStatus);
}
//________________________________________________________________________________

//________________________________________________________________________________checkSerialData()
void checkSerialData() {
  if (Serial.available() > 0) {
    String receivedData = Serial.readStringUntil('\n');
    receivedData.trim();
    
    if (receivedData.length() > 0) {
      Serial.println("Received: " + receivedData);
      parseSerialData(receivedData);
    }
  }
}
//________________________________________________________________________________

//________________________________________________________________________________displayPalmOilCounts()
void displayPalmOilCounts() {
  dmd.selectFont(SystemFont5x7);
  dmd.clearScreen(true);
  
  // Convert counts to char arrays
  char ripeCountStr[10];
  char unripeCountStr[10];
  sprintf(ripeCountStr, "%d", ripeCount);
  sprintf(unripeCountStr, "%d", unripeCount);
  
  // First row: Ripe count
  dmd.drawString(0, 0, "RIPE:", 5, GRAPHICS_NORMAL);
  dmd.drawString(35, 0, ripeCountStr, strlen(ripeCountStr), GRAPHICS_NORMAL);
  
  // Second row: Unripe count
  dmd.drawString(0, 9, "UNRIPE:", 7, GRAPHICS_NORMAL);
  dmd.drawString(47, 9, unripeCountStr, strlen(unripeCountStr), GRAPHICS_NORMAL);
  
  // Display status indicator on the right side
  if (detectionStatus == "running") {
    dmd.drawString(85, 0, "RUN", 3, GRAPHICS_NORMAL);
  } else if (detectionStatus == "paused") {
    dmd.drawString(85, 0, "PAU", 3, GRAPHICS_NORMAL);
  } else if (detectionStatus == "loading") {
    dmd.drawString(85, 0, "LDG", 3, GRAPHICS_NORMAL);
  } else {
    dmd.drawString(85, 0, "STP", 3, GRAPHICS_NORMAL);
  }
}
//________________________________________________________________________________

//________________________________________________________________________________VOID SETUP()
void setup() {
  // put your setup code here, to run once:

  Serial.begin(115200);
  Serial.println();
  Serial.println("ESP32 P10 Palm Oil Detection Display - USB Mode");

  delay(500);

  Serial.println();
  Serial.println("return the clock speed of the CPU.");
  // return the clock speed of the CPU.
  uint8_t cpuClock = ESP.getCpuFreqMHz();
  delay(500);

  Serial.println();
  Serial.println("Timer Begin");
  // Use 1st timer of 4.
  // devide cpu clock speed on its speed value by MHz to get 1us for each signal  of the timer.
  timer = timerBegin(0, cpuClock, true);
  delay(500);

  Serial.println();
  Serial.println("Attach triggerScan function to our timer.");
  // Attach triggerScan function to our timer.
  timerAttachInterrupt(timer, &triggerScan, true);
  delay(500);

  Serial.println();
  Serial.println("Set alarm to call triggerScan function.");
  // Set alarm to call triggerScan function.
  // Repeat the alarm (third parameter).
  timerAlarmWrite(timer, 300, true);
  delay(500);

  Serial.println();
  Serial.println("Start an alarm.");
  // Start an alarm.
  timerAlarmEnable(timer);
  delay(500);

  // Initial display
  displayPalmOilCounts();
  Serial.println("Setup complete");
}
//________________________________________________________________________________

//________________________________________________________________________________VOID LOOP()
void loop() {
  // put your main code here, to run repeatedly:
  
  unsigned long currentTime = millis();
  
  // Check for serial data from computer
  checkSerialData();
  
  // Update display every updateInterval milliseconds
  if (currentTime - lastUpdate >= updateInterval) {
    displayPalmOilCounts();
    lastUpdate = currentTime;
  }
  
  delay(50); // Small delay to prevent excessive processing
}
//________________________________________________________________________________
//<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
