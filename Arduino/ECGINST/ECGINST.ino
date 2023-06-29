#define SENSOR 36// Set the A0 as SENSOR

#define B0 0.4328
#define B1 1.731
#define B2 2.597
#define B3 1.731
#define B4 0.4328
#define A1 2.37
#define A2 2.314
#define A3 1.055
#define A4 0.1874

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
float beatRate = 60;
int movement = 0;
void setup() {
  
  pinMode(SENSOR, INPUT);
  Serial.begin(115200);
  //analogReadResolution(12);
  pinMode(32, INPUT); // Setup for leads off detection LO +
  pinMode(33, INPUT); // Setup for leads off detection LO -
  
}

void loop() {
  float sensor = analogRead(SENSOR);
  float voltage = (sensor / 4095.0) * 1.6;
  
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
  }
  if (voltage > threshold) {
    unsigned long currentBeatTime = millis();
    unsigned long beatPeriod = currentBeatTime - lastBeatTime;
    lastBeatTime = currentBeatTime;

    beatRate = 60.0 / (beatPeriod / 1000.0);
  }
  //Wait for a bit to keep serial data from saturating
  Serial.println(String(voltage) + "," + String(beatRate) + "," + String(movement));
  delay(10);
}
