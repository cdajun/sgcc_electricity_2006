# -*- coding: utf-8 -*-
"""
data_fetcher.py

修复说明（关键）：
- 年度数据抓取失败 → 返回 0
- 月度数据抓取失败 → 返回 []
- 绝不返回 None，防止上层 len() / for 直接崩溃
"""

import time
import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


# =========================
# 年度用电量
# =========================
def get_year_power_usage(driver, userid: str) -> float:
    """
    返回年度用电量（kWh）
    失败时返回 0
    """
    try:
        # 页面跳转逻辑（保持原项目写法）
        time.sleep(2)

        total_ele = driver.find_element(By.CSS_SELECTOR, ".total")
        value = total_ele.text.strip()

        if not value:
            logger.warning(f"Year power usage empty for {userid}")
            return 0

        return float(value)

    except NoSuchElementException as e:
        logger.error(f"The yearly data get failed : {e}")
        return 0

    except Exception as e:
        logger.error(f"Get year power usage for {userid} failed, pass : {e}")
        return 0


# =========================
# 年度电费
# =========================
def get_year_power_charge(driver, userid: str) -> float:
    """
    返回年度电费（元）
    失败时返回 0
    """
    try:
        time.sleep(2)

        total_fee = driver.find_element(By.CSS_SELECTOR, ".total")
        value = total_fee.text.strip()

        if not value:
            logger.warning(f"Year power charge empty for {userid}")
            return 0

        return float(value)

    except NoSuchElementException as e:
        logger.error(f"The yearly charge data get failed : {e}")
        return 0

    except Exception as e:
        logger.error(f"Get year power charge for {userid} failed, pass : {e}")
        return 0


# =========================
# 月度用电量
# =========================
def get_month_power_usage(driver, userid: str) -> list:
    """
    返回月度用电列表
    [
        {"month": "2026-01", "usage": 123.45},
        ...
    ]
    失败时返回 []
    """
    try:
        time.sleep(2)

        result = []

        rows = driver.find_elements(By.CSS_SELECTOR, ".el-table__row")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 2:
                continue

            month = cols[0].text.strip()
            usage = cols[1].text.strip()

            if not month or not usage:
                continue

            result.append({
                "month": month,
                "usage": float(usage)
            })

        return result

    except NoSuchElementException as e:
        logger.error(f"The month data get failed : {e}")
        return []

    except Exception as e:
        logger.error(f"Get month power usage for {userid} failed, pass : {e}")
        return []


# =========================
# 日用电量
# =========================
def get_daily_power_usage(driver, userid: str) -> list:
    """
    返回每日用电数据
    [
        {"date": "2026-01-06", "usage": 16.52},
        ...
    ]
    """
    try:
        time.sleep(2)

        result = []

        rows = driver.find_elements(By.CSS_SELECTOR, ".el-table__row")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 2:
                continue

            date = cols[0].text.strip()
            usage = cols[1].text.strip()

            if not date or not usage:
                continue

            result.append({
                "date": date,
                "usage": float(usage)
            })

        return result

    except Exception as e:
        logger.error(f"Get daily power usage for {userid} failed : {e}")
        return []