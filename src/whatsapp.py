from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import os
import pickle
from io import BytesIO
from utils import (
    send_to_clipboard,
    cache_dir,
    retry,
    dec_wrapper,
    random_intervals,
    class_exc_waiting,
    save_cache,
    load_cache,
)
from PIL import Image

os.environ["WDM_SSL_VERIFY"] = "false"

selenium_folder = os.path.join(cache_dir, "selenium")


class WhatsApp:
    def __init__(self):
        self.image_data = None
        self.driver = None
        self.interval_config = {
            "steps": 6,
            "min_seconds": 6,
            "max_seconds": 8,
            "min_seconds_step": 1,
        }
        self._interval_generator = iter([])

    @property
    def _next_interval(self):
        res = next(self._interval_generator, None)
        if res is None:
            self._interval_generator = iter(
                random_intervals(*self.interval_config.values())
            )
            res = next(self._interval_generator)
        return res

    def set_image_data(self, path):
        image = Image.open(path)

        output = BytesIO()
        image.convert("RGB").save(output, "BMP")

        self.image_data = output.getvalue()[14:]
        output.close()

    def start(self):
        if self.driver:
            self.driver.quit()

        os.makedirs(selenium_folder, exist_ok=True)

        options = webdriver.EdgeOptions()
        options.add_argument(f"user-data-dir={selenium_folder}")

        self.driver = webdriver.Edge(
            service=EdgeService(EdgeChromiumDriverManager().install()), options=options
        )

        cookies = load_cache("cookies", None)
        if cookies is not None:
            for cookie in cookies:
                self.driver.add_cookie(cookie)

        self.driver.get("https://web.whatsapp.com")

        self.actions = ActionChains(self.driver)

    def stop(self):
        save_cache("cookies", self.driver.get_cookies())
        self.driver.quit()

    def check(self, xpath, operator=None, *other_conditions):
        return (
            WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            if operator is None
            else WebDriverWait(self.driver, 15).until(
                operator(
                    EC.element_to_be_clickable((By.XPATH, xpath)),
                    *[
                        condition((By.XPATH, xpath), *args, **kwargs)
                        for condition, args, kwargs in other_conditions
                    ],
                )
            )[0]
        )

    def check_absense(self, xpath, operator=None, *other_conditions):
        return (
            WebDriverWait(self.driver, 15).until_not(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            if operator is None
            else WebDriverWait(self.driver, 15).until_not(
                operator(
                    EC.element_to_be_clickable((By.XPATH, xpath)),
                    *[
                        condition((By.XPATH, xpath), *args, **kwargs)
                        for condition, args, kwargs in other_conditions
                    ],
                )
            )[0]
        )

    def find_and_click(self, xpath, operator=None, *other_conditions):
        element = self.check(xpath, operator, *other_conditions)
        element.click()
        return element

    def do_all_send_image(self, name, phone, text=None):
        self.search_enter()
        self.search_input(phone)
        self.enter_contact(name)
        self.paste_image()
        if text is not None:
            self.paste_image_description(text)
        self.send()  # for debug

    @dec_wrapper(retry, class_exc_waiting, times=3, on_debug=True)
    def search_enter(self):
        xpath_search_enter = r'//*[@id="side"]/div[1]/div/div/div[2]'
        self.find_and_click(xpath_search_enter)

    @class_exc_waiting
    @retry
    def search_input(self, text):
        xpath_search_input = r'//*[@id="side"]/div[1]/div/div/div[2]/div/div[1]/p'

        element_search_input = self.find_and_click(xpath_search_input)

        if input_length := len(element_search_input.text):
            self.actions.send_keys(Keys.BACKSPACE * input_length)
            self.actions.perform()
            element_search_input = self.find_and_click(xpath_search_input)

        self.actions.send_keys_to_element(element_search_input, text)
        self.actions.perform()

        assert element_search_input.text == text

    @class_exc_waiting
    @retry
    def enter_contact(self, name):
        xpath_contact_result_title = (
            f'//*[@id="pane-side"]/div[1]/div/div//span[@title="{name}"]'
        )
        self.find_and_click(xpath_contact_result_title)

        xpath_contact_header = r'//*[@id="main"]/header/div[2]/div/div/div/span'
        self.check(
            xpath_contact_header,
            EC.all_of,
            (EC.text_to_be_present_in_element, (name,), {}),
        )

    @class_exc_waiting
    @retry
    def paste_image(self):
        xpath_input_message_only = (
            r'//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[1]/p'
        )

        element_input_message_only = self.check(xpath_input_message_only)

        send_to_clipboard(self.image_data, "image")

        element_input_message_only.send_keys(Keys.CONTROL, "v")

        xpath_one_image_preview_container = r'//*[@id="app"]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[2]/div[1]/div[count(child::*) = 1]'

        self.check(xpath_one_image_preview_container)

    @class_exc_waiting
    @retry
    def paste_image_description(self, text):
        xpath_input_image_description = r'//*[@id="app"]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[1]/p'

        element_input_image_description = self.check(xpath_input_image_description)

        if input_length := len(element_input_image_description.text):
            self.actions.send_keys(Keys.BACKSPACE * input_length)
            self.actions.perform()
            element_input_image_description = self.check(xpath_input_image_description)

        send_to_clipboard(text)

        element_input_image_description.send_keys(Keys.CONTROL, "v")

    @class_exc_waiting
    @retry
    def send(self):
        xpath_send_button = r'//*[@id="app"]/div/div/div[3]/div[2]/span/div/span/div/div/div[2]/div/div[2]/div[2]/div/div'

        self.find_and_click(xpath_send_button)

        self.check_absense(xpath_send_button)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv, find_dotenv

    _ = load_dotenv(find_dotenv())
    _phone = os.environ["CLEO_ENVIA_PHONE"]
    _name = os.environ["CLEO_ENVIA_NAME"]
    _image = os.environ["CLEO_ENVIA_IMAGE"]
    _text = os.environ["CLEO_ENVIA_TEXT"]

    wpp = WhatsApp()
    wpp.start()
    wpp.set_image_data(_image)
    wpp.do_all_send_image(_name, _phone, _text)
    wpp.stop()
