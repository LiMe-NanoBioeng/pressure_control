from pymodbus.client import ModbusSerialClient
from config import *
conf=config()

class ThermoPlate(ModbusSerialClient):
    def __init__(self, parent=None):
        # Modbus RTUクライアント設定
        self.client = ModbusSerialClient(
            port=conf.THERMO_PLATE_PORT,
            baudrate=9600,
            bytesize=8,
            parity='E',    # Even parity
            stopbits=1,
            timeout=1
        )
        self.SLAVE_ID = 1       # 通信ユニットNo.（デフォルト1）
        self.SV_ADDR  = 0x2103 #address of set point
        self.CR_ADDR=0x2402 #address of current value
           
    def settemp(self,tmp):
        self.SV_VALUE = tmp  # 設定温度
        # 接続開始
        if not self.client.connect():
            print("Connection Failed")
        
        # レジスタに書き込み
        result = self.client.write_register(address=self.SV_ADDR, value=self.SV_VALUE,device_id=1)
        if result.isError():
            print("Writing Failed", result)
        else:
            print("set temperature to {}℃".format(tmp/10))
        self.client.close()
    
    def readtemp(self):
        try:
            result =self.client.read_holding_registers(address=self.CR_ADDR,count=1,device_id=1)
            return float(result.registers[0])/10.0
        except:
            print("error")
            return -1

# TP=ThermoPlate()
# print(TP.readtemp())
# TP.settemp(400)