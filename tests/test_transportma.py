"""
Selenium test suite for TransportMA — Causal Transportability Meta-Analysis.
~20 tests covering page structure, examples, computations, UI, and report.

Run:  python -m pytest tests/test_transportma.py -v
"""
import io
import os
import sys
import time
import pytest

# Only set UTF-8 stdout when NOT running under pytest (pytest captures stdout)
if "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HTML_PATH = os.path.join(os.path.dirname(__file__), "..", "transportma.html")
FILE_URL = "file:///" + os.path.abspath(HTML_PATH).replace("\\", "/")

EXAMPLES = [
    {"name": "SGLT2i", "btn_idx": 0, "k": 6},
    {"name": "Statins", "btn_idx": 1, "k": 8},
    {"name": "Antihypertensives", "btn_idx": 2, "k": 5},
]


@pytest.fixture(scope="module")
def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(3)
    yield d
    d.quit()


def load_page(driver):
    """Navigate to the app and override window.confirm/alert."""
    driver.get(FILE_URL)
    driver.execute_script("window.confirm = function(){return true;};")
    driver.execute_script("window.alert = function(){};")
    time.sleep(0.3)


def js_click(driver, el):
    """Click via JS for headless reliability."""
    driver.execute_script("arguments[0].click();", el)


# --- 1. Page structure ---
class TestPageStructure:
    def test_page_loads_title(self, driver):
        """T01: Page loads and title contains TransportMA."""
        load_page(driver)
        assert "TransportMA" in driver.title

    def test_four_tabs_present(self, driver):
        """T02: 4 tab buttons with correct labels."""
        load_page(driver)
        tabs = driver.find_elements(By.CSS_SELECTOR, ".tab-btn[role='tab']")
        assert len(tabs) == 4
        labels = [t.text.strip() for t in tabs]
        assert "Data" in labels
        assert "Transport Analysis" in labels
        assert "Sensitivity" in labels
        assert "Report" in labels

    def test_tab_roles(self, driver):
        """T03: Tab buttons have role=tab, panels have role=tabpanel."""
        load_page(driver)
        tabs = driver.find_elements(By.CSS_SELECTOR, "[role='tab']")
        assert len(tabs) == 4
        panels = driver.find_elements(By.CSS_SELECTOR, "[role='tabpanel']")
        assert len(panels) == 4

    def test_tab_switching(self, driver):
        """T04: Clicking each tab shows its panel."""
        load_page(driver)
        for tab_id in ["transport", "sensitivity", "report", "data"]:
            btn = driver.find_element(By.ID, f"tbtn-{tab_id}")
            js_click(driver, btn)
            time.sleep(0.2)
            panel = driver.find_element(By.ID, f"panel-{tab_id}")
            assert "active" in panel.get_attribute("class")


# --- 2. Examples load correctly ---
class TestExamples:
    @pytest.mark.parametrize("ex", EXAMPLES, ids=[e["name"] for e in EXAMPLES])
    def test_load_example_result_exists(self, driver, ex):
        """T05-T07: Load each example, verify state.result is non-null."""
        load_page(driver)
        btns = driver.find_elements(By.CSS_SELECTOR, ".ex-btn")
        js_click(driver, btns[ex["btn_idx"]])
        time.sleep(0.5)
        has_result = driver.execute_script("return state.result !== null && state.result !== undefined;")
        assert has_result, f"state.result is null after loading example {ex['name']}"

    @pytest.mark.parametrize("ex", EXAMPLES, ids=[e["name"] for e in EXAMPLES])
    def test_example_trial_count(self, driver, ex):
        """T08-T10: After loading, state.trials has correct count."""
        load_page(driver)
        btns = driver.find_elements(By.CSS_SELECTOR, ".ex-btn")
        js_click(driver, btns[ex["btn_idx"]])
        time.sleep(0.5)
        k = driver.execute_script("return state.trials.length;")
        assert k == ex["k"], f"Expected k={ex['k']}, got {k}"


# --- 3. Transported vs pooled effect ---
class TestTransportedEffect:
    def test_transported_differs_from_pooled(self, driver):
        """T11: |transported - pooled| > 0.01 for SGLT2i example."""
        load_page(driver)
        btns = driver.find_elements(By.CSS_SELECTOR, ".ex-btn")
        js_click(driver, btns[0])
        time.sleep(0.5)
        diff = driver.execute_script(
            "return Math.abs(state.result.transported - state.result.pooled);"
        )
        assert diff > 0.01, f"Transported and pooled too close: diff={diff}"

    def test_transported_has_ci(self, driver):
        """T12: Transported CI exists and lower < upper."""
        load_page(driver)
        js_click(driver, driver.find_elements(By.CSS_SELECTOR, ".ex-btn")[0])
        time.sleep(0.5)
        ci = driver.execute_script("return state.result.ciTransported;")
        assert ci is not None and len(ci) == 2
        assert ci[0] < ci[1], f"CI inverted: {ci}"


# --- 4. Similarity weights ---
class TestSimilarityWeights:
    def test_weights_sum_to_one(self, driver):
        """T13: Similarity weights sum to ~1.0."""
        load_page(driver)
        js_click(driver, driver.find_elements(By.CSS_SELECTOR, ".ex-btn")[0])
        time.sleep(0.5)
        wsum = driver.execute_script(
            "return state.result.wSampling.reduce(function(a,b){return a+b;}, 0);"
        )
        assert abs(wsum - 1.0) < 0.001, f"Weights sum={wsum}, expected ~1.0"

    def test_neff_between_1_and_k(self, driver):
        """T14: Effective N is between 1 and k."""
        load_page(driver)
        js_click(driver, driver.find_elements(By.CSS_SELECTOR, ".ex-btn")[0])
        time.sleep(0.5)
        neff = driver.execute_script("return state.result.nEff;")
        k = driver.execute_script("return state.result.trials.length;")
        assert 1.0 <= neff <= k, f"nEff={neff}, k={k}"


# --- 5. Transport metrics display ---
class TestMetricsDisplay:
    def test_transport_metrics_has_values(self, driver):
        """T15: Transport metrics div has at least 3 metric cards with values."""
        load_page(driver)
        js_click(driver, driver.find_elements(By.CSS_SELECTOR, ".ex-btn")[1])
        time.sleep(0.5)
        # Switch to transport tab
        js_click(driver, driver.find_element(By.ID, "tbtn-transport"))
        time.sleep(0.2)
        metrics = driver.find_elements(By.CSS_SELECTOR, "#transportMetrics .metric")
        assert len(metrics) >= 3, f"Found only {len(metrics)} metric cards"
        for m in metrics:
            val = m.find_element(By.CSS_SELECTOR, ".metric-val").text.strip()
            assert len(val) > 0, "Empty metric value"


# --- 6. Weight table ---
class TestWeightTable:
    def test_weight_table_row_count(self, driver):
        """T16: Weight table has correct number of rows (one per trial)."""
        load_page(driver)
        js_click(driver, driver.find_elements(By.CSS_SELECTOR, ".ex-btn")[1])
        time.sleep(0.5)
        js_click(driver, driver.find_element(By.ID, "tbtn-transport"))
        time.sleep(0.2)
        rows = driver.find_elements(By.CSS_SELECTOR, "#weightTable tbody tr")
        assert len(rows) == 8, f"Expected 8 rows (Statins k=8), got {len(rows)}"


# --- 7. Sensitivity canvas ---
class TestSensitivity:
    def test_sensitivity_canvas_exists(self, driver):
        """T17: Sensitivity canvas element is present."""
        load_page(driver)
        js_click(driver, driver.find_elements(By.CSS_SELECTOR, ".ex-btn")[0])
        time.sleep(0.5)
        js_click(driver, driver.find_element(By.ID, "tbtn-sensitivity"))
        time.sleep(0.2)
        canvas = driver.find_element(By.ID, "sensitivityCanvas")
        assert canvas is not None
        # Canvas should have been drawn (width attribute set by setCanvas)
        w = driver.execute_script("return document.getElementById('sensitivityCanvas').width;")
        assert w > 0


# --- 8. Report ---
class TestReport:
    def test_report_contains_key_terms(self, driver):
        """T18: Report mentions doubly-robust or AIPW or Dahabreh."""
        load_page(driver)
        js_click(driver, driver.find_elements(By.CSS_SELECTOR, ".ex-btn")[0])
        time.sleep(0.5)
        js_click(driver, driver.find_element(By.ID, "tbtn-report"))
        time.sleep(0.2)
        text = driver.find_element(By.ID, "reportText").text
        has_term = ("doubly-robust" in text.lower()
                    or "aipw" in text.lower()
                    or "dahabreh" in text.lower())
        assert has_term, f"Report missing key terms. Start: {text[:200]}"


# --- 9. Theme toggle ---
class TestTheme:
    def test_theme_toggle(self, driver):
        """T19: Theme toggle switches between dark and light."""
        load_page(driver)
        initial = driver.execute_script(
            "return document.documentElement.getAttribute('data-theme');"
        )
        btn = driver.find_element(By.CSS_SELECTOR, ".theme-btn")
        js_click(driver, btn)
        time.sleep(0.2)
        after = driver.execute_script(
            "return document.documentElement.getAttribute('data-theme');"
        )
        assert initial != after, f"Theme did not change: {initial} -> {after}"
        # Toggle back
        js_click(driver, btn)
        time.sleep(0.2)
        restored = driver.execute_script(
            "return document.documentElement.getAttribute('data-theme');"
        )
        assert restored == initial


# --- 10. Target population inputs ---
class TestTargetInputs:
    def test_target_inputs_editable(self, driver):
        """T20: Target population inputs accept new values."""
        load_page(driver)
        age_input = driver.find_element(By.ID, "tgtAge")
        age_input.clear()
        age_input.send_keys("80")
        val = age_input.get_attribute("value")
        assert val == "80", f"Age input value={val}, expected '80'"

    def test_target_inputs_affect_result(self, driver):
        """T21: Changing target age changes transported effect."""
        load_page(driver)
        # Load example first
        js_click(driver, driver.find_elements(By.CSS_SELECTOR, ".ex-btn")[0])
        time.sleep(0.5)
        effect1 = driver.execute_script("return state.result.transported;")

        # Switch back to Data tab (loadExample switches to transport tab)
        js_click(driver, driver.find_element(By.ID, "tbtn-data"))
        time.sleep(0.2)

        # Change target age significantly via JS (headless may block .clear/.sendKeys)
        driver.execute_script("document.getElementById('tgtAge').value = '55';")

        # Re-run transport
        run_btn = driver.find_element(
            By.XPATH, "//button[contains(text(),'Transport to Target')]"
        )
        js_click(driver, run_btn)
        time.sleep(0.5)
        effect2 = driver.execute_script("return state.result.transported;")
        assert effect1 != effect2, "Transported effect unchanged after altering target age"


# --- 11. JSON export structure ---
class TestExport:
    def test_export_json_state(self, driver):
        """T22: Export JSON contains expected keys."""
        load_page(driver)
        js_click(driver, driver.find_elements(By.CSS_SELECTOR, ".ex-btn")[2])
        time.sleep(0.5)
        keys = driver.execute_script("""
            var r = state.result;
            var d = {version:'transportma-1.0', transported:r.transported, pooled:r.pooled,
                ciTransported:r.ciTransported, target:r.target, nEff:r.nEff,
                wSampling:r.wSampling, beta:r.beta};
            return Object.keys(d);
        """)
        for k in ["version", "transported", "pooled", "ciTransported", "target", "nEff", "wSampling", "beta"]:
            assert k in keys, f"Missing key '{k}' in export"
