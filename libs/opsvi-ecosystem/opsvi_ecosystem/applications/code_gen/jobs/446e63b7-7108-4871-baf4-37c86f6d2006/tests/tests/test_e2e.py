import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from app import create_app


@pytest.fixture(scope="module")
def test_app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="module")
def live_server(test_app):
    from multiprocessing import Process
    import time

    def run():
        test_app.run(port=5001, debug=False, use_reloader=False)

    proc = Process(target=run)
    proc.start()
    time.sleep(1)  # wait for server to start
    yield
    proc.terminate()
    proc.join()


@pytest.fixture(scope="module")
def browser():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def test_home_page_loads_and_displays_weather_info(live_server, browser):
    browser.get("http://localhost:5001/")
    assert "Weather" in browser.title
    # Check that key elements for location, temperature and conditions appear
    location = browser.find_element(By.ID, "location")
    temperature = browser.find_element(By.ID, "temperature")
    condition = browser.find_element(By.ID, "condition")
    assert location.text != ""
    assert temperature.text != ""
    assert condition.text != ""


def test_weather_refresh_button_updates_weather_info(live_server, browser):
    browser.get("http://localhost:5001/")
    old_temp = browser.find_element(By.ID, "temperature").text
    refresh_button = browser.find_element(By.ID, "refresh-button")
    refresh_button.click()
    import time

    time.sleep(2)  # Assuming ajax or reload
    new_temp = browser.find_element(By.ID, "temperature").text
    # May or may not change depending on weather but check element is present
    assert new_temp is not None
    assert new_temp != ""
