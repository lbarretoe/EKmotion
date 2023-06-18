#define SENSOR 36// Set the A0 as SENSOR

#define B0 0.662
#define B1 2.648
#define B2 3.972
#define B3 2.648
#define B4 0.662
#define A1 3.181
#define A2 3.861
#define A3 2.112
#define A4 0.4383

float xn_1 = 0;
float xn_2 = 0;
float xn_3 = 0;
float xn_4 = 0;
float yn_1 = 0;
float yn_2 = 0;
float yn_3 = 0;
float yn_4 = 0;

unsigned long lastBeatTime = 0; // Tiempo del último latido detectado
float threshold = 1.0; // Umbral para la detección de picos, ajusta según sea necesario

void setup() {
  
  pinMode(SENSOR, INPUT);
  Serial.begin(115200);
  //analogReadResolution(12);
  pinMode(32, INPUT); // Setup for leads off detection LO +
  pinMode(33, INPUT); // Setup for leads off detection LO -
}

void loop() {
  float sensor = analogRead(SENSOR);
  float voltage = (sensor / 4095.0) * 1.1;
  
  if((digitalRead(32) == 1)||(digitalRead(33) == 1)){
    return;
  }
  else{
    // send the value of analog input 0:
      float y = B0*sensor + B1*xn_1 + B2*xn_2 + B3*xn_3 + B4*xn_4 - yn_1*A1- yn_2*A2 - yn_3*A3 - yn_4*A4;
      xn_4 = xn_3;
      xn_3 = xn_2;
      xn_2 = xn_1;
      xn_1 = sensor;
      yn_4 = yn_3;
      yn_3 = yn_2;
      yn_2 = yn_1;
      yn_1 = y;
      //Serial.println(y);
      //Serial.print(",");
      Serial.println(voltage);
  }
  /*
  if (voltage > threshold) {
    unsigned long currentBeatTime = millis();
    unsigned long beatPeriod = currentBeatTime - lastBeatTime;
    lastBeatTime = currentBeatTime;

    float beatRate = 60.0 / (beatPeriod / 1000.0);
    Serial.println("BPM: " + String(beatRate));
  }
  */
  //Wait for a bit to keep serial data from saturating
  
  delay(10);
}
