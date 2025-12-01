#include <Arduino.h>
#include <Servo.h>

#define SOUND_SPEED 0.034 // Velocidad del sonido en cm/us
#define MAX_DISTANCE 65
#define VELOCITY 255

enum RotationDirection {LEFT, RIGHT};

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
        motor motor_one;
        motor motor_two;
        ultraSonic sonic_sensor;
        servoMotor servo_motor;

    public:
        ArduinoRobot(motor m1, motor m2, ultraSonic us, servoMotor sm);
        ~ArduinoRobot();

        void init();
        void advance(int speed_one, int speed_two);
        void reverse(int speed_one, int speed_two);
        void stop();
        void goLeft(int speed_one, int speed_two);
        void goRight(int speed_one, int speed_two);
        float measure_distance();

        void setServoAngle(int angle);

        RotationDirection chooseTurnDirection();
};


ArduinoRobot::ArduinoRobot(motor m1, motor m2, ultraSonic us, servoMotor sm) : motor_one(m1), motor_two(m2), sonic_sensor(us), servo_motor(sm)
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

    // Servomotor
    servo_motor.servo.attach(servo_motor.servoPin);
    setServoAngle(90);
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

void ArduinoRobot::goLeft(int speed_one, int speed_two){
    // Giro en el lugar: motor izquierdo atrás, motor derecho adelante
    digitalWrite(motor_one.motorIn1, HIGH);
    digitalWrite(motor_one.motorIn2, LOW);
    analogWrite(motor_one.motorEnable, speed_one);

    digitalWrite(motor_two.motorIn1, LOW);
    digitalWrite(motor_two.motorIn2, HIGH);
    analogWrite(motor_two.motorEnable, speed_two);
}

void ArduinoRobot::goRight(int speed_one, int speed_two){
    // Giro en el lugar: motor izquierdo adelante, motor derecho atrás
    digitalWrite(motor_one.motorIn1, LOW);
    digitalWrite(motor_one.motorIn2, HIGH);
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


// Declaracion de pines para componentes
motor motorOne = {4, 3, 2};
motor motorTwo = {6, 7, 5};

ultraSonic sonicSensor = {8, 9};

servoMotor servoMotor = {Servo(), A5};

// Creación del objeto robot
ArduinoRobot robot(motorOne, motorTwo, sonicSensor, servoMotor);

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
