import time
import logging
import requests
import numpy as np
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DataFetcher:

    def __init__(self, ha_url, ha_token):
        self.HA_URL = ha_url
        self.HA_TOKEN = ha_token
        self.DRIVER_IMPLICITY_WAIT_TIME = 10
        self.RETRY_WAIT_TIME_OFFSET_UNIT = 2

    # =========================
    # Home Assistant 同步
    # =========================
    def update_ha_sensor(self, entity_id, state, attributes=None):
        headers = {
            "Authorization": f"Bearer {self.HA_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "state": state,
            "attributes": attributes or {}
        }
        requests.post(
            f"{self.HA_URL}/api/states/{entity_id}",
            headers=headers,
            json=payload,
            timeout=10
        )

    # =========================
    # 电费余额（抓到立刻写 HA）
    # =========================
    def get_electricity_charge_balance(self, driver, userid):
        try:
            balance = driver.find_element(
                By.XPATH, "//span[@class='balance-num']"
            ).text
            balance = float(balance)
            logging.info(
                f"---- Get electricity charge balance for {userid} successfully, balance is {balance} CNY."
            )

            # ⭐ 立刻同步到 HA
            self.update_ha_sensor(
                entity_id=f"sensor.electricity_charge_balance_{userid}",
                state=balance,
                attributes={
                    "unit_of_measurement": "CNY",
                    "device_class": "monetary",
                    "state_class": "total",
                    "friendly_name": "电费余额"
                }
            )

            return balance

        except Exception as e:
            logging.error(f"---- Get electricity charge balance for {userid} failed: {e}")
            return 0

    # =========================
    # 年度数据（不存在直接返回 0）
    # =========================
    def _get_yearly_data(self, driver, userid):
        try:
            target = driver.find_element(By.CLASS_NAME, "total")
            WebDriverWait(driver, self.DRIVER_IMPLICITY_WAIT_TIME).until(
                EC.visibility_of(target)
            )

            usage = driver.find_element(
                By.XPATH, "//ul[@class='total']/li[1]/span"
            ).text
            charge = driver.find_element(
                By.XPATH, "//ul[@class='total']/li[2]/span"
            ).text

        except Exception as e:
            logging.warning("Year data not available yet")
            usage, charge = 0, 0

        # ⭐ 立刻同步到 HA
        self.update_ha_sensor(
            entity_id=f"sensor.electricity_year_usage_{userid}",
            state=usage,
            attributes={
                "unit_of_measurement": "kWh",
                "state_class": "total",
                "friendly_name": "年度用电量"
            }
        )

        self.update_ha_sensor(
            entity_id=f"sensor.electricity_year_charge_{userid}",
            state=charge,
            attributes={
                "unit_of_measurement": "CNY",
                "state_class": "total",
                "friendly_name": "年度电费"
            }
        )

        return usage, charge

    # =========================
    # 月度数据（不存在返回空）
    # =========================
    def _get_month_usage(self, driver, userid):
        try:
            target = driver.find_element(By.CLASS_NAME, "total")
            WebDriverWait(driver, self.DRIVER_IMPLICITY_WAIT_TIME).until(
                EC.visibility_of(target)
            )

            table_text = driver.find_element(
                By.XPATH,
                "//*[@id='pane-first']/div[1]/div[2]/div[2]/div/div[3]/table/tbody"
            ).text

            if not table_text.strip():
                raise ValueError("Empty month table")

            rows = table_text.split("\n")
            if "MAX" in rows:
                rows.remove("MAX")

            if len(rows) < 3:
                raise ValueError("Invalid month data")

            rows = np.array(rows).reshape(-1, 3)
            months, usage, charge = [], [], []

            for r in rows:
                months.append(r[0])
                usage.append(float(r[1]))
                charge.append(float(r[2]))

        except Exception:
            logging.warning("Month data not available yet")
            months, usage, charge = [], [], []

        # ⭐ 立刻同步到 HA
        self.update_ha_sensor(
            entity_id=f"sensor.electricity_month_usage_{userid}",
            state=sum(usage) if usage else 0,
            attributes={
                "months": months,
                "detail_usage": usage,
                "detail_charge": charge,
                "unit_of_measurement": "kWh",
                "state_class": "total",
                "friendly_name": "月度用电量"
            }
        )

        return months, usage, charge

    # =========================
    # 每日数据（原本就正常，补即时同步）
    # =========================
    def sync_daily_usage(self, userid, date, usage):
        self.update_ha_sensor(
            entity_id=f"sensor.electricity_daily_usage_{userid}",
            state=usage,
            attributes={
                "date": date,
                "unit_of_measurement": "kWh",
                "state_class": "measurement",
                "friendly_name": "昨日用电量"
            }
        )