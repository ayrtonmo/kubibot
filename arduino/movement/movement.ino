#include <Arduino.h>
#include <Servo.h>
#include <AFMotor.h>  // Shield tipo V1 / HW130

#define SOUND_SPEED 0.034
#define MAX_DISTANCE 65
#define VELOCITY 150

enum RotationDirection {LEFT, RIGHT};

/**
 * @brief Estructura para definir un sensor ultrasónico
 */
struct ultraSonic
{
    int echoPin; // Pin Echo del sensor
    int trigPin; // Pin Trig del sensor
};

/**
* @brief Estructura para definir el servomotor
*/
struct servoMotor
{
    Servo servo; // Objeto Servo para controlar el servomotor
    int servoPin; // Pin del servomotor
};


class ArduinoRobot
{
    private:
        // Izquierda: M1 + M2 | Derecha: M3 + M4
        AF_DCMotor motor_l1;
        AF_DCMotor motor_l2;
        AF_DCMotor motor_r1;
        AF_DCMotor motor_r2;

    ultraSonic sonic_sensor;
    servoMotor servo_motor;

    int clampSpeed(int s) { return constrain(s, 0, 255); }

    void setLeft(int speed, uint8_t dir){
        speed = clampSpeed(speed);
        motor_l1.setSpeed(speed); motor_l2.setSpeed(speed);
        motor_l1.run(dir);        motor_l2.run(dir);
    }

    void setRight(int speed, uint8_t dir){
        speed = clampSpeed(speed);
        motor_r1.setSpeed(speed); motor_r2.setSpeed(speed);
        motor_r1.run(dir);        motor_r2.run(dir);
    }

    public:
        ArduinoRobot(ultraSonic us, servoMotor sm);
    ~   ArduinoRobot();

    void init();
    void advance(int speed_left, int speed_right);
    void reverse(int speed_left, int speed_right);
    void stop();
    void goLeft(int speed_left, int speed_right);
    void goRight(int speed_left, int speed_right);
    float measure_distance();

    void setServoAngle(int angle);
    RotationDirection chooseTurnDirection();
};

ArduinoRobot::ArduinoRobot(ultraSonic us, servoMotor sm):
    motor_l1(1), motor_l2(2), motor_r1(3), motor_r2(4),
    sonic_sensor(us), servo_motor(sm) {}

ArduinoRobot::~ArduinoRobot() {}

void ArduinoRobot::init(){
    stop();

    pinMode(sonic_sensor.echoPin, INPUT);
    pinMode(sonic_sensor.trigPin, OUTPUT);

    servo_motor.servo.attach(servo_motor.servoPin); // SERVO1 del shield V1 = D10
    setServoAngle(90);
}

void ArduinoRobot::advance(int speed_left, int speed_right){
    setLeft(speed_left, FORWARD);
    setRight(speed_right, FORWARD);
}

void ArduinoRobot::reverse(int speed_left, int speed_right){
    setLeft(speed_left, BACKWARD);
    setRight(speed_right, BACKWARD);
}

void ArduinoRobot::goLeft(int speed_left, int speed_right){
    setLeft(speed_left, BACKWARD);
    setRight(speed_right, FORWARD);
}

void ArduinoRobot::goRight(int speed_left, int speed_right){
    setLeft(speed_left, FORWARD);
    setRight(speed_right, BACKWARD);
}

void ArduinoRobot::stop(){
    motor_l1.run(RELEASE); motor_l2.run(RELEASE);
    motor_r1.run(RELEASE); motor_r2.run(RELEASE);
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

void ArduinoRobot::setServoAngle(int angle){
    servo_motor.servo.write(angle);
}

RotationDirection ArduinoRobot::chooseTurnDirection(){
    float leftDistance, rightDistance;
    float angleOff = 40; // Distancia de precaucion para servo
    // Medir distancia a la izquierda (0 + angleOff°)
    setServoAngle(angleOff);
    leftDistance = measure_distance();
    delay(1000);

    // Medir distancia a la derecha (180 - angleOff°)
    setServoAngle(180 - angleOff);
    rightDistance = measure_distance();
    delay(1000);
    // Volver al centro (90°)
    setServoAngle(90);
    delay(1000);

    Serial.print("Izq: ");
    Serial.print(leftDistance);
    Serial.print(" cm | Der: ");
    Serial.print(rightDistance);
    Serial.println(" cm");

    if(leftDistance > rightDistance){
        Serial.println("Elegido: IZQUIERDA");
        return LEFT;
    }
    else {
        Serial.println("Elegido: DERECHA");
        return RIGHT;
    }
}


// TRIG=A0, ECHO=A1  (ojo: tu struct es {echoPin, trigPin})
ultraSonic sonicSensor = {A1, A0};

// SERVO1 del shield V1/HW130 = pin digital 10
servoMotor servoMotor = {Servo(), 10};

// Robot con 4 motores (M1..M4)
ArduinoRobot robot(sonicSensor, servoMotor);

bool isChoosingPath = false;
RotationDirection chosenDirection;
unsigned long reverseStartTime = 0;
unsigned long turnStartTime = 0;

enum State {ADVANCING, REVERSING, TURNING, DETAINED};
State currentState = ADVANCING;

void setup(){
    Serial.begin(9600);
    robot.init();
}



void loop(){

    float distance = robot.measure_distance();

    switch(currentState){
        case ADVANCING:
            if(distance < MAX_DISTANCE){
                Serial.println("obstaculo detectado a " + String(distance) + " cm, revirtiendo...");
                currentState = REVERSING;
                reverseStartTime = millis();
                robot.stop();
            }
            else {
                robot.advance(VELOCITY, VELOCITY);
            }
            break;

        case REVERSING:
            if(distance < MAX_DISTANCE){
                robot.reverse(VELOCITY, VELOCITY);
            }
            else {
                robot.stop();
                Serial.println("Analizando camino...");
                chosenDirection = robot.chooseTurnDirection();
                currentState = TURNING;
                turnStartTime = millis();
            }
            break;

        case TURNING:
            if(millis() - turnStartTime < 1500){ // Girar 1.5 segundos
                if(chosenDirection == LEFT){
                    robot.goLeft(VELOCITY, VELOCITY);
                }
                else {
                    robot.goRight(VELOCITY, VELOCITY);
                }
            }
            else {
                Serial.println("Reanudando avance\n");
                currentState = ADVANCING;
            }
            break;

        case DETAINED:
            robot.stop();
            break;
    }

    delay(100);
}
