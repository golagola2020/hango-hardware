'''
    @ Hango Project
    @ This raspberry.py file is the main file of the Hango Project
'''    

# 외장모듈
import os, sys                  # 시스템 모듈
import serial                   # 직렬 통신 모듈

# 경로설정
sys.path.append('/home/pi/hango-hardware/hardware/raspberry/module')

# 내장모듈
from module.config import *
from module.Http import Http
from module.DataManager import DataManager
from module.Speak import Gspeak
from module.Serial import Serial
    
# 메인 함수
def main():
    # 아두이노와 시리얼 통신할 인스턴스 생성 
    port = serial.Serial(
        port = PORT,
        baudrate = 9600
    )
    # 캐시 비우기
    port.flushInput()

    # 인스턴스 생성
    data_manager = DataManager()    # 음료 데이터 관리용 인스턴스
    speak = Gspeak(25100)           # gTTS를 사용하여 Hango 음성 출력을 제공하는 인스턴스 => 인자는 음성 출력 속도

    # 음료수 정보 요청
    response = Http.request_drinks(SERIAL_NUMBER)
    data_manager.refresh_drinks(response)

    # 초기 사운드 메세지 설정
    drinks = data_manager.get_drinks()
    speak.refresh_message(drinks)

    # 설정된 메세지 오브젝트 불러오기
    sound_msgs = speak.get_sound_msgs()

    # 음료수 이름을 파일명으로하는 사운드 만들고 저장
    for file_path in sound_msgs.keys() :
        for file_name, message in sound_msgs[file_path].items() :
            speak.save_sound(file_path, file_name, message)

    # 무한 반복
    while True:
        # 아두이노 센싱 데이터 한 줄 단위로 수신
        receive = Serial.get_receive_data(port)

        # 이용 가능한 데이터인지 검사
        if Serial.is_available(receive) :
            # 아두이노 수신 데이터 저장
            Serial.save_received_data(receive)
            received_keys = Serial.get_received_keys()

            # 아두이노 센싱 데이터 불러오기
            sensings = Serial.get_sensings()
            
            # 라즈베리파이가 가공할 데이터를 모두 수신 했다면 실행 
            if BASIC_KEYS.difference(received_keys) == set() :

                # 아두이노에서 센싱된 데이터가 있으면 실행 
                if sensings["success"] :
                    # 출력
                    print("센싱 데이터 수신 성공")
                    
                    # 판매된 음료수가 있을 경우에 실행
                    if sensings["sold_position"] != -1 :
                        # 감지 정보가 새로운 감지 정보와 다르면 실행 => 같은 말을 반복하지 않기 위함
                        if Serial.current_sensing_data != sensings["sold_position"] :
                            # 새로 감지된 정보 저장 => 같은 말을 반복하지 않기 위함
                            Serial.current_sensing_data = sensings["sold_position"]

                            drink = {
                                'name' : drinks["name"][sensings["sold_position"]],
                                'price' : drinks["price"][sensings["sold_position"]],
                                'sold_position' : sensings["sold_position"]
                            }

                            # 판매된 음료수 정보 차감 요청
                            print("판매된 음료 차감 데이터를 요청하고 스피커 출력을 실행합니다.")
                            response = Http.update_sold_drink(USER_ID, SERIAL_NUMBER, drink)
                            data_manager.check_drink_update(response)

                            # 스피커 출력
                            print("스피커 출력을 실행합니다.")
                            speak.stop()
                            speak.say("sold", drinks["name"][sensings["sold_position"]])
                            
                    # 손이 음료 버튼에 위치했을 경우에 실행
                    elif sensings["sensed_position"] != -1 :
                        # 감지 정보가 새로운 감지 정보와 다르면 실행 => 같은 말을 반복하지 않기 위함
                        if Serial.current_sensing_data != sensings["sensed_position"] :
                            # 새로 감지된 정보 저장 => 같은 말을 반복하지 않기 위함
                            Serial.current_sensing_data = sensings["sensed_position"]

                            # speak.exit()
                            speak.stop()
                            print("물체가 감지되어 스피커 출력을 실행합니다.")

                            # 해당 음료가 품절일 경우 실행
                            if drinks["count"][sensings["sensed_position"]] <= 0 :
                                # 스피커 출력
                                speak.say("sold_out", drinks["name"][sensings["sensed_position"]])
                            else :
                                # 스피커 출력
                                speak.say("position", drinks["name"][sensings["sensed_position"]])
                            
                    # 수신한 변수명 집합 비우기 => 다음 센싱 때에도 정상 수신하는지 검사하기 위함 
                    received_keys.clear()
            
            # 음성 출력이 가능하면 실행 => 이미 음성이 출력 중일 땐 실행되지 않는다.
            if "success" in sensings and speak.is_available():

                # 음료수 정보 요청
                print("센싱 데이터가 없습니다.\n서버로부터 음료 정보를 불러옵니다...")
                response = Http.request_drinks(SERIAL_NUMBER)
                data_manager.refresh_drinks(response)

                # 수정된 음료수가 있다면 사운드 파일 업데이트
                drinks = data_manager.get_drinks()
                speak.update_message(drinks)

                # 스피커 출력
                print("스피커 출력을 실행합니다.\n:인사말 ")
                speak.stop()
                speak.say("basic")
        else :
            print("수신 가능한 센싱 데이터가 아닙니다.")
                


# 파일이 직접 실행됐다면 (모듈로써 사용된게 아니라면) 실행
if __name__ == "__main__":
    main()