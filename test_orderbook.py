
import unittest

from OrderBook import OrderBook


class TestOrderBook(unittest.TestCase):

    def setUp(self):
        self.book = OrderBook()

    def test_limit_buy_resting(self):
        report = self.book.add_limit_buy(99, 5, "T1")

        self.assertEqual(report["status"], "RESTING")
        self.assertEqual(report["remaining_quantity"], 5)
        self.assertTrue(self.book.validate_order_book())

    def test_limit_sell_resting(self):
        report = self.book.add_limit_sell(101, 5, "T1")

        self.assertEqual(report["status"], "RESTING")
        self.assertEqual(report["remaining_quantity"], 5)
        self.assertTrue(self.book.validate_order_book())

    def test_full_buy_execution(self):
        self.book.add_limit_sell(100, 5, "T1")

        report = self.book.add_limit_buy(100, 5, "T2")

        self.assertEqual(report["status"], "FILLED")
        self.assertEqual(report["filled_quantity"], 5)
        self.assertEqual(report["remaining_quantity"], 0)
        self.assertTrue(self.book.validate_order_book())

    def test_partial_buy_execution(self):
        self.book.add_limit_sell(100, 3, "T1")

        report = self.book.add_limit_buy(100, 5, "T2")

        self.assertEqual(report["status"], "PARTIALLY_FILLED")
        self.assertEqual(report["filled_quantity"], 3)
        self.assertEqual(report["remaining_quantity"], 2)
        self.assertTrue(self.book.validate_order_book())


    def test_full_sell_execution(self):
        self.book.add_limit_buy(100, 5, "T1")

        report = self.book.add_limit_sell(100, 5, "T2")

        self.assertEqual(report["status"], "FILLED")
        self.assertEqual(report["filled_quantity"], 5)
        self.assertEqual(report["remaining_quantity"], 0)
        self.assertTrue(self.book.validate_order_book())

    def test_partial_sell_execution(self):
        self.book.add_limit_buy(100, 3, "T1")

        report = self.book.add_limit_sell(100, 5, "T2")

        self.assertEqual(report["status"], "PARTIALLY_FILLED")
        self.assertEqual(report["filled_quantity"], 3)
        self.assertEqual(report["remaining_quantity"], 2)
        self.assertTrue(self.book.validate_order_book())

    def test_market_buy(self):
        self.book.add_limit_sell(100, 3, "T1")
        self.book.add_limit_sell(101, 2, "T2")

        report = self.book.market_buy("T3",5)

        self.assertEqual(report["filled_quantity"], 5)
        self.assertEqual(report["unfilled_quantity"], 0)
        self.assertAlmostEqual(
            report["average_execution_price"], 100.4
        )
        self.assertTrue(self.book.validate_order_book())

    def test_market_sell(self):
        self.book.add_limit_buy(100, 3, "T1")
        self.book.add_limit_buy(99, 2, "T2")

        report = self.book.market_sell("T3",5)

        self.assertEqual(report["filled_quantity"], 5)
        self.assertEqual(report["unfilled_quantity"], 0)
        self.assertAlmostEqual(
            report["average_execution_price"], 99.6
        )
        self.assertTrue(self.book.validate_order_book())

    def test_order_history_after_full_fill(self):
        self.book.add_limit_sell(100, 5, "T1")

        report = self.book.add_limit_buy(100, 5, "T2")

        order_id = report["order_id"]
        order = self.book.order_history[order_id]

        self.assertEqual(order.status, "FILLED")
        self.assertEqual(order.original_quantity, 5)
        self.assertEqual(order.filled_quantity, 5)
        self.assertEqual(order.quantity, 0)
        self.assertNotIn(order_id, self.book.order_map)

    def test_cancellation(self):
        report = self.book.add_limit_buy(99, 5, "T1")
        order_id = report["order_id"]

        self.assertFalse(self.book.cancel_order(order_id, "T2"))
        self.assertTrue(self.book.cancel_order(order_id, "T1"))

        self.assertEqual(
            self.book.order_history[order_id].status, "CANCELED"
        )
        self.assertNotIn(order_id, self.book.order_map)
        self.assertTrue(self.book.validate_order_book())

    def test_fifo_priority(self):
     self.book.add_limit_sell(100, 2, "T1")
     self.book.add_limit_sell(100, 3, "T2")

     report = self.book.market_buy("T3", 4)

     self.assertEqual(report["filled_quantity"], 4)

    # T1 should be completely filled
     self.assertEqual(
        self.book.order_history[1].status, "FILLED"
    )

    # T2 should have 1 unit remaining
     self.assertEqual(
        self.book.order_history[2].quantity, 1
    )

     self.assertTrue(self.book.validate_order_book())

    def test_price_priority(self):
     self.book.add_limit_sell(105, 2, "T1")
     self.book.add_limit_sell(102, 3, "T2")
     self.book.add_limit_sell(103, 2, "T3")

     report = self.book.market_buy("T4", 3)

     self.assertEqual(report["filled_quantity"], 3)

     self.assertEqual(
        self.book.order_history[2].status, "FILLED"
    )

     self.assertEqual(
        self.book.order_history[1].quantity, 2
    )

     self.assertEqual(
        self.book.order_history[3].quantity, 2
    )

     self.assertTrue(self.book.validate_order_book())

if __name__ == "__main__":
    unittest.main()

