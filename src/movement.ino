#include <Arduino.h>
#include <Servo.h>

#define SOUND_SPEED 0.034 // Velocidad del sonido en cm/us

/**
 * @brief Estructura para definir un motor
 *
 */
struct motor
{
	int motorIn1; // Input 1 del motor
	int motorIn2; // Input 2 del motor
	int motorEnable; // Input Enable del motor
};

/**
 * @brief Estructura para definir un sensor ultrasónico
 */
struct ultraSonic
{
	int echoPin; // Pin Echo del sensor
	int trigPin; // Pin Trig del sensor
};

// Declaracion de pines para componentes
motor motorOne = {3, 4, 2};
motor motorTwo = {6, 7, 5};

ultraSonic sonicSensor = {8, 9};


/**
 * @brief Funcion para avanzar el motor
 *
 * @param motorIn1 Input 1 del motor
 * @param motorIn2 Input 2 del motor
 * @param motorEnable Input Enable del motor
 * @param speed Velocidad del motor (0-255)
 */
void advance_motor(int motorIn1, int motorIn2, int motorEnable, int speed){
  	digitalWrite(motorIn1, LOW);
  	digitalWrite(motorIn2, HIGH);
  	analogWrite(motorEnable, speed);
}

/**
 * @brief Funcion para retroceder el motor
 *
 * @param motorIn1 Input 1 del motor
 * @param motorIn2 Input 2 del motor
 * @param motorEnable Input Enable del motor
 * @param speed Velocidad del motor (0-255)
 */
void reverse_motor(int motorIn1, int motorIn2, int motorEnable, int speed){
  	digitalWrite(motorIn1, HIGH);
  	digitalWrite(motorIn2, LOW);
  	analogWrite(motorEnable, speed);
}

/**
 * @brief Funcion para obtener la distancia medida por el sensor ultrasónico
 *
 * @return float Distancia medida en cm
 */
float measure_distance(int echoPin, int trigPin){
	digitalWrite(trigPin, LOW);
	delayMicroseconds(2);
	digitalWrite(trigPin, HIGH);
	delayMicroseconds(10);
	digitalWrite(trigPin, LOW);

	int duration = pulseIn(echoPin, HIGH);
	int distance = (duration*SOUND_SPEED)/2;

	Serial.print("Distance: ");
	Serial.print(distance);
	Serial.println(" cm");

	return distance;
}

void setup(){
	// Motores DC
  	pinMode(motorOne.motorIn1, OUTPUT);
  	pinMode(motorOne.motorIn2, OUTPUT);
  	pinMode(motorOne.motorEnable, OUTPUT);

  	pinMode(motorTwo.motorIn1, OUTPUT);
  	pinMode(motorTwo.motorIn2, OUTPUT);
  	pinMode(motorTwo.motorEnable, OUTPUT);

	// Sensor ultrasónico
	pinMode(sonicSensor.echoPin, INPUT);
	pinMode(sonicSensor.trigPin, OUTPUT);

	Serial.begin(9600);
}

void loop(){

	// Medir distancia y avanzar o retroceder según la distancia medida
	float distance = measure_distance(sonicSensor.echoPin, sonicSensor.trigPin);

	if (distance < 20){
		Serial.println("Avanzando");
		advance_motor(motorOne.motorIn1, motorOne.motorIn2, motorOne.motorEnable, 0);
		advance_motor(motorTwo.motorIn1, motorTwo.motorIn2, motorTwo.motorEnable, 0);
		delay(1000);
	}
	else{
		Serial.println("Retrocediendo");
		advance_motor(motorOne.motorIn1, motorOne.motorIn2, motorOne.motorEnable, 255);
		advance_motor(motorTwo.motorIn1, motorTwo.motorIn2, motorTwo.motorEnable, 255);
		delay(1000);
	}

}
