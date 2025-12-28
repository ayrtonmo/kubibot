/**
 * @file arduino.ino
 * @author Iván Mansilla, Ayrton Morrison
 * @brief Código que maneja el movimiento autónomo y sistema de detección de obstáculos de Kubibot. Se utilizan 4 motores DC, un sensor ultrasónico y un servomotor.
 *
 */
#include <Arduino.h>
#include <Servo.h>
#include <AFMotor.h>

#define SOUND_SPEED 0.034 //!< Velocidad del sonido
#define MAX_DISTANCE 65 //!< Distancia máxima para detectar obstáculos (cm)
#define VELOCITY 150 //!< Velocidad de los motores (0-255)
#define TURN_TIME 1500 //!< Tiempo de giro (ms)

#define SENSOR_ECHO_PIN A1 //!< Pin ECHO del sensor ultrasónico
#define SENSOR_TRIG_PIN A0 //!< Pin TRIG del sensor ultrasónico
#define SERVO_PIN 10 //!< Pin del servomotor

#define SERVO_OFFSET 20 //!< Offset para restar al ángulo del servomotor
#define SERVO_SECURITY_OFFSET 40 //!< Offset de seguridad al girar el servomotor

/**
 * @brief Direcciones de rotación para el robot
 */
enum RotationDirection {LEFT, RIGHT};

/**
 * @brief Estados de movimiento del robot
 */
enum State {ADVANCING, REVERSING, TURNING, DETAINED};

/**
 * @brief Estructura para definir un sensor ultrasónico
 */
struct ultraSonic
{
    int echoPin; //!< Pin ECHO del sensor
    int trigPin; //!< Pin TRIG del sensor
};

/**
* @brief Estructura para definir el servomotor
*/
struct servoMotor
{
    Servo servo; //!< Objeto Servo para controlar el servomotor
    int servoPin; //!< Pin del servomotor
};

/**
 * @brief Clase para manejar la comunicación con Raspberry Pi
 *
 */
class RaspberryPi
{
    private:
        bool stop; //!< Indica si el robot debe detenerse

    public:
        RaspberryPi(): stop(false) {}
        ~RaspberryPi(){}

        void setStop(bool s){
            stop = s;
        }
        bool getStop(){
            return stop;
        }
        // S para detener, R para reanudar
        void readStopCommand(){
            if (Serial.available() > 0) {
                int command = Serial.read();
                if(command == 'S'){
                    setStop(true);
                }
                else if(command == 'R'){
                    setStop(false);
                }
            }
        }
};

/**
 * @brief Clase para controlar el robot Arduino con motores DC, sensor ultrasónico y servomotor
 *
 */
class ArduinoRobot
{
    private:
        AF_DCMotor motor_l1; //!< Motor izquierdo-adelante
        AF_DCMotor motor_l2; //!< Motor izquierdo-atrás
        AF_DCMotor motor_r1; //!< Motor derecho-atrás
        AF_DCMotor motor_r2; //!< Motor derecho-adelante

        ultraSonic sonic_sensor; //!< Sensor ultrasónico
        servoMotor servo_motor; //!< Servomotor

        /**
         * @brief Limita la velocidad del motor al rango válido (0-255)
         *
         * @param s Velocidad a validar
         * @return int Velocidad limitada
         */
        int clampSpeed(int s){
            return constrain(s, 0, 255);
        }

        /**
         * @brief Configura la velocidad y dirección de los motores izquierdos (M1 M2)
         *
         * @param speed Velocidad del motor (0-255)
         * @param dir Dirección del motor (FORWARD/BACKWARD/RELEASE)
         */
        void setLeft(int speed, uint8_t dir){
            speed = clampSpeed(speed);
            motor_l1.setSpeed(speed);
            motor_l2.setSpeed(speed);
            motor_l1.run(dir);
            motor_l2.run(dir);
        }

        /**
         * @brief Configura la velocidad y dirección de los motores derechos (M3 M4)
         *
         * @param speed
         * @param dir
         */
        void setRight(int speed, uint8_t dir){
            speed = clampSpeed(speed);
            motor_r1.setSpeed(speed);
            motor_r2.setSpeed(speed);
            motor_r1.run(dir);
            motor_r2.run(dir);
        }

    public:
        /**
         * @brief Constructor del robot Arduino
         *
         * @param us Sensor ultrasónico
         * @param sm Servomotor
         */
        ArduinoRobot(ultraSonic us, servoMotor sm):
            motor_l1(1), motor_l2(2), motor_r1(3), motor_r2(4),
            sonic_sensor(us), servo_motor(sm) {}

        /**
         * @brief Destructor del robot Arduino
         *
         */
        ~ArduinoRobot(){}

        /**
         * @brief Inicializa los componentes del robot
         *
         */
        void init(){
            stop();

            pinMode(sonic_sensor.echoPin, INPUT);
            pinMode(sonic_sensor.trigPin, OUTPUT);

            servo_motor.servo.attach(servo_motor.servoPin);
            setServoAngle(90);
        }

        /**
         * @brief Avanza hacia adelante el robot
         *
         * @param speed_left Velocidad de los motores izquierdos
         * @param speed_right Velocidad de los motores derechos
         */
        void advance(int speed_left, int speed_right){
            setLeft(speed_left, BACKWARD);
            setRight(speed_right, BACKWARD);
        }

        /**
         * @brief Avanza hacia atrás el robot
         *
         * @param speed_left
         * @param speed_right
         */
        void reverse(int speed_left, int speed_right){
            setLeft(speed_left, FORWARD);
            setRight(speed_right, FORWARD);
        }

        /**
         * @brief Detiene el movimiento del robot
         *
         */
        void stop(){
                motor_l1.run(RELEASE);
                motor_l2.run(RELEASE);
                motor_r1.run(RELEASE);
                motor_r2.run(RELEASE);
        }

        /**
         * @brief Gira el robot hacia la izquierda
         *
         * @param speed_left Velocidad de los motores izquierdos
         * @param speed_right Velocidad de los motores derechos
         */
        void goLeft(int speed_left, int speed_right){
            setLeft(speed_left, FORWARD);
            setRight(speed_right, BACKWARD);
        }

        /**
         * @brief Gira el robot hacia la derecha
         *
         * @param speed_left Velocidad de los motores izquierdos
         * @param speed_right Velocidad de los motores derechos
         */
        void goRight(int speed_left, int speed_right){
            setLeft(speed_left, BACKWARD);
            setRight(speed_right, FORWARD);
        }

        /**
         * @brief Mide la distancia utilizando el sensor ultrasónico
         *
         * @return float Distancia medida en centímetros
         */
        float measure_distance(){
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

        /**
         * @brief Establece el ángulo del servomotor
         *
         * @param angle Ángulo en grados (0-180)
         */
        void setServoAngle(int angle){
            int adjustedAngle = constrain(angle - SERVO_OFFSET, 0, 180);
            servo_motor.servo.write(adjustedAngle);
        }

        /**
         * @brief Escoge la dirección de giro basada en las mediciones del sensor ultrasónico
         *
         * @return RotationDirection Dirección de giro elegida (LEFT/RIGHT)
         */
        RotationDirection chooseTurnDirection(){
            float leftDistance, rightDistance;
            // Medir distancia a la izquierda (0 + SERVO_SECURITY_OFFSET°)
            setServoAngle(SERVO_SECURITY_OFFSET);
            leftDistance = measure_distance();
            delay(1000);

            // Medir distancia a la derecha (180 - angleOff°)
            setServoAngle(180 - SERVO_SECURITY_OFFSET);
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
};

/**
 * @brief Inicialización de variables globales
 *
 */
ultraSonic sonicSensor = {SENSOR_ECHO_PIN, SENSOR_TRIG_PIN};
servoMotor servoMotor = {Servo(), SERVO_PIN};
ArduinoRobot robot(sonicSensor, servoMotor);
RaspberryPi raspberryPi;

RotationDirection chosenDirection;
unsigned long turnStartTime = 0;

float distance = 0.0;

State currentState = ADVANCING;

/**
 * @brief Inicialización del arduino
 *
 */
void setup(){
    Serial.begin(9600);
    robot.init();
}

/**
 * @brief Loop principal de control del robot
 *
 */
void loop(){
    raspberryPi.readStopCommand();
    if(raspberryPi.getStop()){
        currentState = DETAINED;
    }
    else if(currentState == DETAINED){
        Serial.println("Reanudando operaciones...");
        currentState = ADVANCING;
    }

    distance = robot.measure_distance();

    switch(currentState){
        case ADVANCING:
            if(distance < MAX_DISTANCE){
                Serial.println("obstaculo detectado a " + String(distance) + " cm, revirtiendo...");
                currentState = REVERSING;
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
            if(millis() - turnStartTime < TURN_TIME){
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
