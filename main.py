import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time

from config import Config
from email_sender import send_email

class CourseSelector:
    def __init__(self, driver_path, url, account, password):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.service = Service(driver_path)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
        
        self.url = url
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
            self.logger.info("Login success")
        else:
            self.logger.warning("Login failed", alert_text)
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
    
    def filter_courses(self, time_span='', course_name_exp=''):
        """
        Filter courses based on time span and/or course name.
        :param time_span: The desired time span for the course
        :param course_name_exp: The desired course name (or part of it)
        :return: List of filtered courses
        """
        self.driver.implicitly_wait(1)
        records = self.driver.find_elements(By.CSS_SELECTOR, "tr.record2, tr.hi_line")
        filtered_records = records[::2]  # Select every other record to avoid duplicates
        
        self.logger.debug(f'Total courses: {len(filtered_records)}')
        
        results = []
        for record in filtered_records:
            course_name = record.find_element(By.XPATH, './td[4]/a[1]').text
            span_value = record.find_element(By.XPATH, './td[6]/span').text
            font_value = record.find_element(By.XPATH, './td[8]/font').text

            if '代表隊專長訓練' in course_name:
                continue
            
            if self._should_include_course(record, time_span, course_name_exp):
                self.logger.info(f'Filtered Course: {course_name}, Time: {span_value}, Availability: {font_value}')
                results.append([course_name, font_value, span_value])
            else:
                self.logger.debug(f"Course: {course_name}, Time: {span_value}, Availability: {font_value}")
        
        return results

    def _should_include_course(self, record, time_span, course_name_exp):
        return (self._filter_by_time_span(record, time_span) and
                self._filter_by_course_name(record, course_name_exp) and
                self._is_course_available(record))
    
    def _filter_by_time_span(self, record, time_span):
        """Filter a record based on the given time span."""
        span_value = record.find_element(By.XPATH, './td[6]/span').text
        return time_span in span_value

    def _filter_by_course_name(self, record, course_name):
        """Filter a record based on the given course name."""
        actual_course_name = record.find_element(By.XPATH, './td[4]/a[1]').text
        return course_name in actual_course_name if course_name else True

    def _is_course_available(self, record):
        """Check if the course has available slots."""
        font_value = record.find_element(By.XPATH, './td[8]/font').text
        comp_font_value = font_value.split('/')
        return comp_font_value[0] != comp_font_value[1]
    
    def store_result(self, results):
        message_templet = """目前釋出名額有：\n"""
        for result in results:
            message_templet += "課程名稱：" + result[0] + "\n目前人數：" + result[1] + "\n時段：" + result[2] + "\n\n"
        return message_templet

    def close(self):
        self.driver.quit()

logger = logging.getLogger(__name__)

def main():
    config = Config()

    if logger.handlers:
        logger.handlers.clear()
    url = 'https://portalfun.yzu.edu.tw/cosSelect/index.aspx'
    driver_path = config.args.driver_path
    account = config.args.username
    password = config.args.password

    selector = CourseSelector(driver_path, url, account, password)
    selector.open_page()

    check_code = selector.get_check_code()
    if check_code:
        logger.debug(f"CheckCode: {check_code}")

        selector.login(check_code)

        # 興趣體育
        coures_name = "體育"
        selector.select_courses('113,1  ', '904', '2') 
        results = selector.filter_courses()
        
        # 自訂
        # coures_name = "網路安全"
        # selector.select_courses(year_value='113,1  ', dept_value='701', degree_value='3')
        # results = selector.filter_courses(time_span="308", course_name_exp=coures_name)


        if results:
            logger.info("有課程")
            message_templet = selector.store_result(results)
            logger.info(message_templet)
            send_email(
                subject=f"{coures_name}課程有空位!!",
                body=message_templet,
                sender_email=config.args.sender_email,
                password=config.args.sender_password,
                receiver_email=config.args.receiver_email,
                # cc_emails=[],
            )
        else:
            logger.info("沒有課程")
            selector.close()
            return

    else:
        logger.error("未能找到 CheckCode cookie")

    selector.close()

if __name__ == '__main__':
    while True:
        main()
        time.sleep(300)
