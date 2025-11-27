#include <Arduino.h>
#include <Servo.h>

#define SOUND_SPEED 0.034 // Velocidad del sonido en cm/us
#define MAX_DISTANCE 65

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
    setServoAngle(90); // ✅ Corregido
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
    
    // Medir distancia a la izquierda (0°)
    setServoAngle(0);
    delay(500);
    leftDistance = measure_distance();
    
    // Medir distancia a la derecha (180°)
    setServoAngle(180);
    delay(500);
    rightDistance = measure_distance();
    
    // Volver al centro (90°)
    setServoAngle(90);
    delay(500);
    
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

servoMotor servoMotor = {Servo(), 10};

// Creación del objeto robot
ArduinoRobot robot(motorOne, motorTwo, sonicSensor, servoMotor);

bool isChoosingPath = false;
RotationDirection chosenDirection; // ✅ Guardar dirección elegida
unsigned long reverseStartTime = 0;
unsigned long turnStartTime = 0;

enum State {ADVANCING, REVERSING, TURNING}; // ✅ Máquina de estados
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
                Serial.println("¡Obstáculo detectado!");
                currentState = REVERSING;
                reverseStartTime = millis();
                robot.stop();
            }
            else {
                robot.advance(200, 200);
            }
            break;
            
        case REVERSING:
            if(millis() - reverseStartTime < 1000){
                robot.reverse(200, 200);
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
                    robot.goLeft(200, 200);
                }
                else {
                    robot.goRight(200, 200);
                }
            }
            else {
                Serial.println("Reanudando avance\n");
                currentState = ADVANCING;
            }
            break;
    }
    
    delay(50);
}
