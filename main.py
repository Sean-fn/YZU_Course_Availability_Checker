from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
#from dotenv import load_dotenv
import os


class CourseSelector:
    def __init__(self, driver_path, url, account, password):
        self.service = Service(driver_path)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')  # 啟用無介面模式
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
        
        self.url = url
        #load_dotenv()
        #self.account = os.getenv('ACCOUNT')
        #self.password = os.getenv('PASSWORD')
        self.account = account
        self.password = password


    def open_page(self):
        self.driver.get(self.url)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'imgChkCode')))

    def get_check_code(self):
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] == 'CheckCode':
                return cookie['value']
        return None

    def login(self, check_code):
        captcha_input = self.driver.find_element(By.NAME, 'Code')
        captcha_input.send_keys(check_code)
        
        account_input = self.driver.find_element(By.NAME, 'uid')
        account_input.send_keys(self.account)

        password_input = self.driver.find_element(By.NAME, 'pwd')
        password_input.send_keys(self.password)

        submit_button = self.driver.find_element(By.ID, 'Button1')
        submit_button.click()

        WebDriverWait(self.driver, 10).until(EC.alert_is_present())
        alert = self.driver.switch_to.alert
        alert_text = alert.text
        if "Login Success" in alert_text:
            print("登入成功")
        else:
            print("登入失敗，Alert 文本:", alert_text)
        alert.accept()

    def select_courses(self, year_value, dept_value, degree_value):
        self.driver.get(self.url)
        
        year_select = self.driver.find_element(By.ID, 'DDL_YM')
        select_year = Select(year_select)
        select_year.select_by_value(year_value)

        dept_select = self.driver.find_element(By.ID, 'DDL_Dept')
        select_dept = Select(dept_select)
        select_dept.select_by_value(dept_value)

        degree_select = self.driver.find_element(By.ID, 'DDL_Degree')
        select_deg = Select(degree_select)
        select_deg.select_by_value(degree_value)

        submit_button = self.driver.find_element(By.ID, 'Button1')
        submit_button.click()

    def filter_courses(self, time_span='\n'):
        self.driver.implicitly_wait(1)
        records = self.driver.find_elements(By.CSS_SELECTOR, "tr.record2, tr.hi_line")
        filtered_records = [record for index, record in enumerate(records) if index % 2 == 0]

        print('課程數量：', len(filtered_records))
        for record in filtered_records:
            span_value = record.find_element(By.XPATH, './td[6]/span').text
            print('指定時段：', span_value)
            font_value = record.find_element(By.XPATH, './td[8]/font').text
            print('人數：', font_value)
            course_name = record.find_element(By.XPATH, './td[4]/a[1]').text
            print('課程名稱：', course_name)
            print('---')

        
        results = []
        for record in filtered_records:
            span_value = record.find_element(By.XPATH, './td[6]/span').text
            if time_span not in span_value:
                continue
            font_value = record.find_element(By.XPATH, './td[8]/font').text
            comp_font_value = font_value.split('/')

            if comp_font_value[0] != comp_font_value[1]:
                course_name = record.find_element(By.XPATH, './td[4]/a[1]').text
                if "表隊專長訓練" in course_name:   # 排除表隊專長訓練
                    continue
                print('課程名稱：', course_name)
                print('指定時段：', span_value)
                print('人數：', font_value)
                print('---')
                results.append([course_name, font_value, span_value])
        return results
    
    def store_result(self, results):
        message_templet = """目前釋出名額有：\n"""
        with open('result.txt', 'r+') as f:
            for result in results:
                if result[0] in f:
                    continue
                f.write(f"{result[0]} {result[1]} {result[2]}\n")
                message_templet += "課程名稱：" + result[0] + "\n目前人數：" + result[1] + "\n時段：" + result[2] + "\n"
        return message_templet

    def close(self):
        self.driver.quit()

# 使用方式

def main():
    driver_path = '/Users/sean/chromedriver-mac-arm64/chromedriver'
    url = 'https://portalfun.yzu.edu.tw/cosSelect/index.aspx'
    #account = os.getenv('ACCOUNT')
    #password = os.getenv('PASSWORD')

    
    selector = CourseSelector(driver_path, url, account, password)
    selector.open_page()

    check_code = selector.get_check_code()
    if check_code:
        # print(f"CheckCode: {check_code}")

        selector.login(check_code)
        # selector.select_courses('113,1  ', '904', '2') #興趣體育
        # results = selector.filter_courses()
        
        selector.select_courses(year_value='113,1  ', dept_value='700', degree_value='1')
        results = selector.filter_courses(time_span="203")


        message_templet = selector.store_result(results)
        print(message_templet)
    else:
        print("未能找到 CheckCode cookie")

    selector.close()

if __name__ == '__main__':
    main()
