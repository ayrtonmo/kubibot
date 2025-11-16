#include <Arduino.h>
#include <Servo.h>

#define SOUND_SPEED 0.034 // Velocidad del sonido en cm/us
#define MAX_DISTANCE 65


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


class ArduinoRobot
{
private:
    motor motor_one;
    motor motor_two;
    ultraSonic sonic_sensor;

public:
    ArduinoRobot(motor m1, motor m2, ultraSonic us);
    ~ArduinoRobot();

    void init();
    void advance(int speed_one, int speed_two);
    void reverse(int speed_one, int speed_two);
    void stop();
    float measure_distance();
};

ArduinoRobot::ArduinoRobot(motor m1, motor m2, ultraSonic us) : motor_one(m1), motor_two(m2), sonic_sensor(us)
{
}

ArduinoRobot::~ArduinoRobot()
{
}

void ArduinoRobot::init(){
    // Motores DC
    pinMode(motor_one.motorIn1, OUTPUT);
    pinMode(motor_one.motorIn2, OUTPUT);
    pinMode(motor_one.motorEnable, OUTPUT);

    pinMode(motor_two.motorIn1, OUTPUT);
    pinMode(motor_two.motorIn2, OUTPUT);
    pinMode(motor_two.motorEnable, OUTPUT);

    // Sensor ultrasonico
    pinMode(sonic_sensor.echoPin, INPUT);
    pinMode(sonic_sensor.trigPin, OUTPUT);
}

void ArduinoRobot::advance(int speed_one, int speed_two){
    digitalWrite(motor_one.motorIn1, LOW);
    digitalWrite(motor_one.motorIn2, HIGH);
    analogWrite(motor_one.motorEnable, speed_one);

    digitalWrite(motor_two.motorIn1, LOW);
    digitalWrite(motor_two.motorIn2, HIGH);
    analogWrite(motor_two.motorEnable, speed_two);
}

void ArduinoRobot::reverse(int speed_one, int speed_two){
    digitalWrite(motor_one.motorIn1, HIGH);
    digitalWrite(motor_one.motorIn2, LOW);
    analogWrite(motor_one.motorEnable, speed_one);

    digitalWrite(motor_two.motorIn1, HIGH);
    digitalWrite(motor_two.motorIn2, LOW);
    analogWrite(motor_two.motorEnable, speed_two);
}

void ArduinoRobot::stop(){
    analogWrite(motor_one.motorEnable, 0);
    analogWrite(motor_two.motorEnable, 0);
}

float ArduinoRobot::measure_distance(){
    digitalWrite(sonic_sensor.trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(sonic_sensor.trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(sonic_sensor.trigPin, LOW);

    long duration = pulseIn(sonic_sensor.echoPin, HIGH);
    float distance = (duration * SOUND_SPEED) / 2;

    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.println(" cm");

    return distance;
}


// Declaracion de pines para componentes
motor motorOne = {4, 3, 2};
motor motorTwo = {6, 7, 5};

ultraSonic sonicSensor = {8, 9};

// Creación del objeto robot
ArduinoRobot robot(motorOne, motorTwo, sonicSensor);


void setup(){
    Serial.begin(9600);
    robot.init();
}

void loop(){

    // Mide distancia y avanza o se detiene segun lo medido
    float distance = robot.measure_distance();

    if (distance < MAX_DISTANCE){
        Serial.println("Deteniendose");
        robot.stop();
        delay(1000);
    }
    else{
        Serial.println("Avanzando");
        // Se ponen estos valores para compensar velocidades de los motores
        robot.advance(150, 255);
        delay(1000);
    }

}
