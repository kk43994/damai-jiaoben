"""
Unit tests for damai_app_v2.py (Mobile v2)
"""
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import pytest

# Add damai_appium to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'damai_appium'))

from config import Config


class TestConfig:
    """Test Config class"""

    def test_config_attributes(self):
        """Test Config object has all required attributes"""
        config = Config(
            server_url="http://127.0.0.1:4723",
            keyword="test_keyword",
            users=["user1", "user2"],
            city="Beijing",
            date="10.01",
            price="599",
            price_index=1,
            if_commit_order=True
        )

        assert config.server_url == "http://127.0.0.1:4723"
        assert config.keyword == "test_keyword"
        assert config.users == ["user1", "user2"]
        assert config.city == "Beijing"
        assert config.date == "10.01"
        assert config.price == "599"
        assert config.price_index == 1
        assert config.if_commit_order == True

    def test_config_load_from_file(self, tmp_path):
        """Test Config.load_config() loads from config.jsonc"""
        # Create a temporary config file
        config_file = tmp_path / "config.jsonc"
        config_content = """
{
  "server_url": "http://localhost:4723",
  "keyword": "test_concert",
  "users": ["Alice", "Bob"],
  "city": "Shanghai",
  "date": "11.11",
  "price": "799",
  "price_index": 2,
  "if_commit_order": false
}
"""
        config_file.write_text(config_content, encoding='utf-8')

        # Change to temp directory and load config
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            config = Config.load_config()

            assert config.server_url == "http://localhost:4723"
            assert config.keyword == "test_concert"
            assert config.users == ["Alice", "Bob"]
            assert config.city == "Shanghai"
            assert config.date == "11.11"
            assert config.price == "799"
            assert config.price_index == 2
            assert config.if_commit_order == False
        finally:
            os.chdir(original_dir)


class TestDamaiBotMocked:
    """Test DamaiBot class with mocked driver"""

    @pytest.fixture
    def mock_driver(self):
        """Create a mock driver"""
        driver = MagicMock()
        driver.update_settings = MagicMock()
        return driver

    @pytest.fixture
    def mock_wait(self):
        """Create a mock WebDriverWait"""
        return MagicMock()

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = Mock()
        config.server_url = "http://127.0.0.1:4723"
        config.keyword = "test"
        config.users = ["user1", "user2"]
        config.city = "Beijing"
        config.date = "10.01"
        config.price = "599"
        config.price_index = 1
        config.if_commit_order = True
        return config

    def test_bot_initialization(self, mock_config, mock_driver, mock_wait):
        """Test DamaiBot initialization"""
        with patch('damai_app_v2.Config.load_config', return_value=mock_config):
            with patch('damai_app_v2.webdriver.Remote', return_value=mock_driver):
                with patch('damai_app_v2.WebDriverWait', return_value=mock_wait):
                    from damai_app_v2 import DamaiBot
                    bot = DamaiBot()

                    # Verify attributes
                    assert bot.config == mock_config
                    assert bot.driver == mock_driver
                    assert bot.wait == mock_wait

                    # Verify driver settings were updated
                    mock_driver.update_settings.assert_called_once()

    def test_ultra_fast_click_success(self, mock_config, mock_driver, mock_wait):
        """Test ultra_fast_click method succeeds"""
        # Setup mock element
        mock_element = MagicMock()
        mock_element.rect = {'x': 100, 'y': 200, 'width': 50, 'height': 30}

        # Mock wait to return element
        mock_wait.until = MagicMock(return_value=mock_element)

        with patch('damai_app_v2.Config.load_config', return_value=mock_config):
            with patch('damai_app_v2.webdriver.Remote', return_value=mock_driver):
                with patch('damai_app_v2.WebDriverWait', return_value=mock_wait):
                    from damai_app_v2 import DamaiBot
                    from selenium.webdriver.common.by import By

                    bot = DamaiBot()
                    bot.wait = mock_wait

                    # Test ultra_fast_click
                    result = bot.ultra_fast_click(By.ID, "test_id", timeout=1.5)

                    assert result == True
                    # Verify click was executed
                    mock_driver.execute_script.assert_called_once()
                    call_args = mock_driver.execute_script.call_args
                    assert call_args[0][0] == "mobile: clickGesture"
                    assert 'x' in call_args[0][1]
                    assert 'y' in call_args[0][1]

    def test_ultra_fast_click_timeout(self, mock_config, mock_driver, mock_wait):
        """Test ultra_fast_click handles timeout"""
        from selenium.common.exceptions import TimeoutException

        # Mock wait to raise TimeoutException
        mock_wait.until = MagicMock(side_effect=TimeoutException())

        with patch('damai_app_v2.Config.load_config', return_value=mock_config):
            with patch('damai_app_v2.webdriver.Remote', return_value=mock_driver):
                with patch('damai_app_v2.WebDriverWait', return_value=mock_wait):
                    from damai_app_v2 import DamaiBot
                    from selenium.webdriver.common.by import By

                    bot = DamaiBot()
                    bot.wait = mock_wait

                    # Test ultra_fast_click with timeout
                    result = bot.ultra_fast_click(By.ID, "test_id", timeout=1.5)

                    assert result == False

    def test_batch_click(self, mock_config, mock_driver, mock_wait):
        """Test batch_click method"""
        # Setup mock elements
        mock_element1 = MagicMock()
        mock_element1.rect = {'x': 100, 'y': 200, 'width': 50, 'height': 30}
        mock_element2 = MagicMock()
        mock_element2.rect = {'x': 150, 'y': 250, 'width': 50, 'height': 30}

        # Mock wait to return elements
        mock_wait.until = MagicMock(side_effect=[mock_element1, mock_element2])

        with patch('damai_app_v2.Config.load_config', return_value=mock_config):
            with patch('damai_app_v2.webdriver.Remote', return_value=mock_driver):
                with patch('damai_app_v2.WebDriverWait', return_value=mock_wait):
                    with patch('damai_app_v2.time.sleep'):  # Mock sleep to speed up test
                        from damai_app_v2 import DamaiBot
                        from selenium.webdriver.common.by import By

                        bot = DamaiBot()
                        bot.wait = mock_wait

                        # Test batch_click
                        elements_info = [
                            (By.ID, "element1"),
                            (By.ID, "element2")
                        ]
                        bot.batch_click(elements_info, delay=0.1)

                        # Verify both elements were clicked
                        assert mock_driver.execute_script.call_count == 2

    def test_ultra_batch_click(self, mock_config, mock_driver, mock_wait):
        """Test ultra_batch_click collects coordinates then clicks"""
        # Setup mock elements
        mock_elements = []
        for i in range(3):
            elem = MagicMock()
            elem.rect = {'x': 100 + i*50, 'y': 200, 'width': 50, 'height': 30}
            mock_elements.append(elem)

        # Mock wait to return elements
        mock_wait.until = MagicMock(side_effect=mock_elements)

        with patch('damai_app_v2.Config.load_config', return_value=mock_config):
            with patch('damai_app_v2.webdriver.Remote', return_value=mock_driver):
                with patch('damai_app_v2.WebDriverWait', return_value=mock_wait):
                    with patch('damai_app_v2.time.sleep'):  # Mock sleep
                        from damai_app_v2 import DamaiBot
                        from appium.webdriver.common.appiumby import AppiumBy

                        bot = DamaiBot()
                        bot.wait = mock_wait

                        # Test ultra_batch_click
                        elements_info = [
                            (AppiumBy.ANDROID_UIAUTOMATOR, 'user1'),
                            (AppiumBy.ANDROID_UIAUTOMATOR, 'user2'),
                            (AppiumBy.ANDROID_UIAUTOMATOR, 'user3')
                        ]
                        bot.ultra_batch_click(elements_info, timeout=2)

                        # Verify all 3 elements were clicked
                        assert mock_driver.execute_script.call_count == 3

    def test_smart_wait_and_click_first_selector(self, mock_config, mock_driver, mock_wait):
        """Test smart_wait_and_click succeeds with first selector"""
        mock_element = MagicMock()
        mock_element.rect = {'x': 100, 'y': 200, 'width': 50, 'height': 30}
        mock_wait.until = MagicMock(return_value=mock_element)

        with patch('damai_app_v2.Config.load_config', return_value=mock_config):
            with patch('damai_app_v2.webdriver.Remote', return_value=mock_driver):
                with patch('damai_app_v2.WebDriverWait', return_value=mock_wait):
                    from damai_app_v2 import DamaiBot
                    from selenium.webdriver.common.by import By

                    bot = DamaiBot()
                    bot.wait = mock_wait

                    # Test with backup selectors
                    backup_selectors = [
                        (By.XPATH, "//*[@id='backup1']"),
                        (By.XPATH, "//*[@id='backup2']")
                    ]
                    result = bot.smart_wait_and_click(
                        By.ID, "primary_selector",
                        backup_selectors=backup_selectors
                    )

                    assert result == True
                    mock_driver.execute_script.assert_called_once()

    def test_smart_wait_and_click_fallback_selector(self, mock_config, mock_driver, mock_wait):
        """Test smart_wait_and_click falls back to backup selector"""
        from selenium.common.exceptions import TimeoutException

        # First selector times out, second succeeds
        mock_element = MagicMock()
        mock_element.rect = {'x': 100, 'y': 200, 'width': 50, 'height': 30}
        mock_wait.until = MagicMock(side_effect=[TimeoutException(), mock_element])

        with patch('damai_app_v2.Config.load_config', return_value=mock_config):
            with patch('damai_app_v2.webdriver.Remote', return_value=mock_driver):
                with patch('damai_app_v2.WebDriverWait', return_value=mock_wait):
                    from damai_app_v2 import DamaiBot
                    from selenium.webdriver.common.by import By

                    bot = DamaiBot()
                    bot.wait = mock_wait

                    # Test with backup selectors
                    backup_selectors = [(By.XPATH, "//*[@id='backup']")]
                    result = bot.smart_wait_and_click(
                        By.ID, "primary_selector",
                        backup_selectors=backup_selectors
                    )

                    assert result == True
                    # Should try twice (primary + backup)
                    assert mock_wait.until.call_count == 2


class TestPerformanceOptimizations:
    """Test v2 performance optimization features"""

    def test_click_gesture_parameters(self):
        """Verify mobile: clickGesture uses optimized parameters"""
        # This test verifies the click gesture configuration
        mock_driver = MagicMock()

        from damai_app_v2 import DamaiBot
        with patch('damai_app_v2.Config.load_config'):
            with patch('damai_app_v2.webdriver.Remote', return_value=mock_driver):
                with patch('damai_app_v2.WebDriverWait'):
                    bot = DamaiBot()

                    # Simulate a click
                    mock_element = MagicMock()
                    mock_element.rect = {'x': 100, 'y': 200, 'width': 50, 'height': 30}

                    with patch.object(bot, 'wait') as mock_wait:
                        mock_wait.until = MagicMock(return_value=mock_element)
                        bot.ultra_fast_click('by', 'value')

                        # Verify click gesture was called with duration: 50
                        call_args = mock_driver.execute_script.call_args
                        if call_args:
                            gesture_params = call_args[0][1]
                            assert gesture_params['duration'] == 50, "Click duration should be 50ms for speed"

    def test_driver_settings_optimization(self):
        """Verify driver settings are optimized for performance"""
        mock_driver = MagicMock()

        from damai_app_v2 import DamaiBot
        with patch('damai_app_v2.Config.load_config'):
            with patch('damai_app_v2.webdriver.Remote', return_value=mock_driver):
                with patch('damai_app_v2.WebDriverWait'):
                    bot = DamaiBot()

                    # Verify update_settings was called with optimizations
                    mock_driver.update_settings.assert_called_once()
                    settings = mock_driver.update_settings.call_args[0][0]

                    # Check key performance settings
                    assert settings['waitForIdleTimeout'] == 0, "Should not wait for idle"
                    assert settings['actionAcknowledgmentTimeout'] == 0, "Should not wait for acknowledgment"
                    assert settings['keyInjectionDelay'] == 0, "Should have no injection delay"
                    assert settings['waitForSelectorTimeout'] == 300, "Should use optimized selector timeout"
                    assert settings['enableNotificationListener'] == False, "Should disable notifications"


class TestConfigurationValues:
    """Test configuration value handling"""

    def test_price_index_handling(self):
        """Test price_index is properly handled"""
        config = Config(
            server_url="http://127.0.0.1:4723",
            keyword="test",
            users=["user1"],
            city="Beijing",
            date="10.01",
            price="599",
            price_index=5,  # Test with actual config value
            if_commit_order=True
        )

        assert config.price_index == 5
        assert isinstance(config.price_index, int)

    def test_users_list_handling(self):
        """Test users list is properly handled"""
        users = ["User1", "User2", "User3"]
        config = Config(
            server_url="http://127.0.0.1:4723",
            keyword="test",
            users=users,
            city="Beijing",
            date="10.01",
            price="599",
            price_index=1,
            if_commit_order=True
        )

        assert len(config.users) == 3
        assert config.users == users
        assert isinstance(config.users, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
