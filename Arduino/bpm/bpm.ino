#define ECG_PIN 36
#define THRESHOLD 3000

unsigned long lastBeatTime = 0;
bool beatDetected = false;
float bpm = 0.0;


void setup() {
  pinMode(ECG_PIN, INPUT);
  Serial.begin(115200);
}

void loop() {
  int ecgValue = analogRead(ECG_PIN);

  // Detecta un latido cuando la señal cruza el umbral
  if (ecgValue > THRESHOLD && !beatDetected) {
    beatDetected = true;
    
    unsigned long currentBeatTime = millis();
    
    // Cálcula el BPM
    if (lastBeatTime > 0) {
      bpm = 60000.0 / (currentBeatTime - lastBeatTime);
      
      // Imprime el valor del ECG y el BPM
    }

    lastBeatTime = currentBeatTime;
  } 
  // Restablece la detección del latido cuando la señal cae por debajo del umbral
  else if (ecgValue <= THRESHOLD) {
    beatDetected = false;
  }
  Serial.print(ecgValue);
  Serial.print(",");
  Serial.print(bpm);
  Serial.print(",");
  Serial.println("0");
  delay(1); // Agrega un retardo de 10 ms entre cada muestreo
}