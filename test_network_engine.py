import unittest
from network_engine import NetworkHealingEngine

class NetworkHealingEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = NetworkHealingEngine()

    def test_fault_creates_alarm_and_degrades_device(self):
        result = self.engine.simulate_fault("RTR-01", "high_latency")
        self.assertTrue(result["ok"])
        self.assertEqual(result["device"]["status"], "Degraded")
        self.assertEqual(result["alarm"]["status"], "Active")

    def test_healing_restores_device(self):
        result = self.engine.simulate_fault("SW-02", "packet_loss")
        healed = self.engine.heal_alarm(result["alarm"]["id"])
        self.assertTrue(healed["ok"])
        self.assertEqual(healed["device"]["status"], "Healthy")
        self.assertEqual(healed["alarm"]["status"], "Healed")

    def test_rejects_unknown_fault(self):
        result = self.engine.simulate_fault("RTR-01", "bad_fault")
        self.assertFalse(result["ok"])

if __name__ == "__main__":
    unittest.main()
