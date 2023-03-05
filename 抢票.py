# encoding:utf-8
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException

# 为什么需要把driver放在外面作为全局变量？
# 因为如果放在里面，driver将会随着对象的销毁而被销毁
# 而我们的train的对象是放在main函数中执行的，只要main函数运行完成后，里面所有的变量将被销毁
service = Service('D:\chromedriver\chromedriver.exe')
driver = webdriver.Chrome(service=service)


class train(object):
    # 登录界面的url
    login_url = "https://kyfw.12306.cn/otn/resources/login.html"
    # 个人界面的url
    personal_url = "https://kyfw.12306.cn/otn/view/index.html"
    # 选择地点时间界面的url
    left_tickets = "https://kyfw.12306.cn/otn/leftTicket/init?"
    # 提交订单界面的url
    confirm_url = "https://kyfw.12306.cn/otn/confirmPassenger/initDc"

    def __init__(self, from_station, to_station, time_data, train_number, name):
        self.from_station = from_station
        self.to_station = to_station
        self.time_data = time_data
        self.train_number = train_number
        self.name = name
        self.select_number = None

        # 初始化站点所对应的代号
        self.station_codes = {}
        self.init_station_code()

    # 先抓取所有站点的代号并保存在.csv文件中
    def init_station_code(self):
        with open("station.csv", 'r', encoding='GBK') as fp:
            reader = csv.DictReader(fp)
            for line in reader:
                name = line['name']
                code = line['code']
                # 获取站点的代号
                self.station_codes[name] = code

    def login(self):
        driver.get(self.login_url)
        # 进入登录界面后用手机扫码登录，等待url变成个人中心的url，判断是否登陆成功
        WebDriverWait(driver, 100).until(
            EC.url_to_be(self.personal_url)
        )

    def search_ticket(self):
        driver.get(self.left_tickets)

        # 起始站的代号设置
        from_station_input = driver.find_element(by=By.ID, value="fromStation")
        from_station_code = self.station_codes[self.from_station]
        driver.execute_script("arguments[0].value='%s'" % from_station_code, from_station_input)

        # 终点站的代号设置
        to_station_input = driver.find_element(by=By.ID, value="toStation")
        to_station_code = self.station_codes[self.to_station]
        driver.execute_script("arguments[0].value='%s'" % to_station_code, to_station_input)

        # 设置时间
        train_date_input = driver.find_element(by=By.ID, value="train_date")
        driver.execute_script("arguments[0].value='%s'" % self.time_data, train_date_input)

        # 执行查询操作
        search_btn = driver.find_element(by=By.ID, value="query_ticket")
        search_btn.click()

        # 解析车次信息
        WebDriverWait(driver, 1000).until(
            EC.presence_of_element_located((By.XPATH, "//tbody[@id='queryLeftTable']/tr"))
        )
        train_trs = driver.find_elements(by=By.XPATH, value="//tbody[@id='queryLeftTable']/tr[not(@datatran)]")

        # 定义一个变量，当选取到所需的座位时使变量变成True
        searched = False

        # 当提取进入界面的时候还不可以预定车票，这时候就要一直循环，知道点击预定车票后退出循环
        while 1:
            # 获得所有车票的信息
            for train_tr in train_trs:
                infos = train_tr.text.replace("\n", " ").split(" ")
                number = infos[0]

                # 从所有车票信息中选取自己所要的车票
                if number in self.train_number:
                    seat_types = self.train_number[number]
                    for seat_type in seat_types:

                        # 选取座位
                        if seat_type == "O":
                            count = infos[9]
                            if count.isdigit() or count == "有":
                                searched = True
                                break
                        elif seat_type == "M":
                            count = infos[8]
                            if count.isdigit() or count == "有":
                                searched = True
                                break

                    # 找到车票后执行点击操作
                    if searched:
                        self.select_number = number
                        order_btn = train_tr.find_element(by=By.XPATH, value=".//a[@class='btn72']")
                        order_btn.click()
                        # 找到车票预定后退出
                        return


def confirm_passengers(self):
    # 显式等待进入提交订单的url及乘客标签显示
    WebDriverWait(driver, 1000).until(
        EC.url_contains(self.confirm_url)
    )
    WebDriverWait(driver, 1000).until(
        EC.presence_of_element_located((By.XPATH, "//ul[@id='normal_passenger_id']/li/label"))
    )

    # 确认需要购票的乘客
    passenger_labels = driver.find_elements(by=By.XPATH, value="//ul[@id='normal_passenger_id']/li/label")
    for passenger_label in passenger_labels:
        name = passenger_label.text
        if name == self.name:
            passenger_label.click()

    # 确认需要购买的席位信息（因为所在html段里含有select属性，所以需要使用Select）
    seat_select = Select(driver.find_element(by=By.ID, value="seatType_1"))
    seat_types = self.train_number[self.select_number]
    for seat_type in seat_types:
        try:
            seat_select.select_by_value(seat_type)
        except NoSuchElementException:
            continue
        else:
            break

    # 等待提交按钮可以点击
    WebDriverWait(driver, 1000).until(
        EC.element_to_be_clickable((By.ID, "submitOrder_id"))
    )
    # 点击提交订单
    submit_btn = driver.find_element(by=By.ID, value="submitOrder_id")
    submit_btn.click()

    # 判断对话框出现及确认按钮可以点击
    WebDriverWait(driver, 1000).until(
        EC.presence_of_element_located((By.CLASS_NAME, "dhtmlx_window_active"))
    )
    WebDriverWait(driver, 1000).until(
        EC.element_to_be_clickable((By.ID, "qr_submit_id"))
    )
    # 执行点击操作
    submit_btn = driver.find_element(by=By.ID, value="qr_submit_id")

    # 有时候会出现点击一次没反应的情况，这时候我们需要循环点击，直到退出点击所在对话框为止
    while submit_btn:
        try:
            submit_btn.click()
            submit_btn = driver.find_element(by=By.ID, value="qr_submit_id")
        except ElementNotVisibleException:
            break


def run(self):
    # 1.登录
    self.login()
    # 2.车票余票查询
    self.search_ticket()
    # 3.确认乘客及车次信息
    self.confirm_passengers()


def main(self):
    fromstation = input("请输入起始站：")
    tostation = input("请输入终点站:")
    time_train = input("请输入订购车票时间（如2022-03-16）：")
    person = input("请输入购票人姓名：")

    # 传参：起始站、终点站、时间、车次及所需座位（O为二等座、M为一等座）、购票人姓名
    # 在spider里面手动更改自己所需的车次及座位类别
    spider = train(fromstation, tostation, time_train, {"D7137": ["O", "M"]}, person)
    spider.run()


if __name__ == '__main__':
    main()
