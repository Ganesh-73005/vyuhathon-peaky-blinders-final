"""
Beautiful PDF Report Generation Service
Generates aesthetic PDF reports with charts, graphs, and professional design
"""

import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import fitz  # PyMuPDF
from loguru import logger
import base64


class PDFReportService:
    """Service for generating beautiful PDF reports"""
    
    # Color scheme - Modern and professional
    COLORS = {
        "primary": (41, 128, 185),      # Blue
        "secondary": (52, 73, 94),      # Dark Blue
        "success": (39, 174, 96),       # Green
        "warning": (243, 156, 18),      # Orange
        "danger": (231, 76, 60),        # Red
        "light": (236, 240, 241),       # Light Gray
        "dark": (44, 62, 80),           # Dark Gray
        "white": (255, 255, 255),
        "text": (52, 73, 94),
    }
    
    def __init__(self):
        self.page_width = 595  # A4 width in points
        self.page_height = 842  # A4 height in points
        self.margin = 40
        
    async def generate_business_report(
        self,
        user_data: Dict[str, Any],
        stock_data: List[Dict[str, Any]],
        sales_data: List[Dict[str, Any]],
        analytics: Dict[str, Any]
    ) -> bytes:
        """Generate a comprehensive business report PDF"""
        
        try:
            # Create PDF document
            doc = fitz.open()
            
            # Page 1: Cover Page
            self._add_cover_page(doc, user_data)
            
            # Page 2: Business Summary
            self._add_summary_page(doc, user_data, analytics)
            
            # Page 3: Sales Analysis
            self._add_sales_page(doc, sales_data, analytics)
            
            # Page 4: Stock Analysis
            self._add_stock_page(doc, stock_data, analytics)
            
            # Page 5: Charts and Graphs
            self._add_charts_page(doc, sales_data, analytics)
            
            # Convert to bytes
            pdf_bytes = doc.write()
            doc.close()
            
            logger.info("PDF report generated successfully")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            raise
    
    def _add_cover_page(self, doc: fitz.Document, user_data: Dict[str, Any]):
        """Add professional cover page"""
        page = doc.new_page(width=self.page_width, height=self.page_height)
        
        # Background gradient effect (using rectangles)
        for i in range(0, 300, 10):
            opacity = 0.1 - (i / 3000)
            page.draw_rect(
                fitz.Rect(0, i, self.page_width, i + 10),
                color=self._normalize_color(self.COLORS["primary"]),
                fill=self._normalize_color(self.COLORS["primary"]),
                fill_opacity=opacity
            )
        
        # Shop name (large, centered)
        shop_name = user_data.get("shop_name", "Business Report")
        self._insert_centered_text(page, 250, shop_name, 36, bold=True,
                                   color=self._normalize_color(self.COLORS["primary"]))

        # Report title
        self._insert_centered_text(page, 300, "Business Performance Report", 20, bold=False,
                                   color=self._normalize_color(self.COLORS["secondary"]))

        # Date range
        date_str = datetime.now().strftime("%B %d, %Y")
        self._insert_centered_text(page, 350, f"Generated on {date_str}", 12, bold=False,
                                   color=self._normalize_color(self.COLORS["text"]))
        
        # Business type badge
        business_type = user_data.get("business_type", "General Store").replace("_", " ").title()
        badge_rect = fitz.Rect(self.page_width / 2 - 80, 380, self.page_width / 2 + 80, 410)
        page.draw_rect(badge_rect, color=self._normalize_color(self.COLORS["success"]),
                      fill=self._normalize_color(self.COLORS["success"]))
        self._insert_centered_text(page, 400, business_type, 14, bold=True,
                                   color=self._normalize_color(self.COLORS["white"]))

        # Footer with location
        location = user_data.get("location", {})
        location_str = f"{location.get('city', 'N/A')}, {location.get('state', 'N/A')}"
        self._insert_centered_text(page, self.page_height - 50, location_str, 10, bold=False,
                                   color=self._normalize_color(self.COLORS["text"]))
    
    def _normalize_color(self, color_tuple):
        """Normalize RGB color from 0-255 to 0-1 range"""
        return tuple(c / 255 for c in color_tuple)

    def _insert_text(self, page: fitz.Page, pos: tuple, text: str, fontsize: int,
                    bold: bool = False, color: tuple = None):
        """Insert text with proper font handling"""
        if color is None:
            color = self._normalize_color(self.COLORS["text"])

        # Use built-in fonts
        fontname = "Helvetica-Bold" if bold else "Helvetica"
        page.insert_text(pos, text, fontsize=fontsize, fontname=fontname, color=color)

    def _insert_centered_text(self, page: fitz.Page, y: float, text: str, fontsize: int,
                             bold: bool = False, color: tuple = None):
        """Insert centered text on the page"""
        if color is None:
            color = self._normalize_color(self.COLORS["text"])

        # Calculate text width (approximate)
        text_width = len(text) * fontsize * 0.5
        x = (self.page_width - text_width) / 2

        # Use the helper method
        self._insert_text(page, (x, y), text, fontsize, bold, color)

    def _add_summary_page(self, doc: fitz.Document, user_data: Dict[str, Any], analytics: Dict[str, Any]):
        """Add business summary page with key metrics"""
        page = doc.new_page(width=self.page_width, height=self.page_height)

        y_pos = self.margin

        # Header
        y_pos = self._add_page_header(page, "Business Summary", y_pos)
        y_pos += 20

        # Key metrics cards
        metrics = [
            {
                "label": "Total Revenue (7 Days)",
                "value": f"₹{analytics.get('total_revenue', 0):,.2f}",
                "color": self.COLORS["success"],
                "icon": "💰"
            },
            {
                "label": "Total Transactions",
                "value": str(analytics.get('total_transactions', 0)),
                "color": self.COLORS["primary"],
                "icon": "📊"
            },
            {
                "label": "Stock Items",
                "value": str(analytics.get('stock_items_count', 0)),
                "color": self.COLORS["warning"],
                "icon": "📦"
            },
            {
                "label": "Stock Value",
                "value": f"₹{analytics.get('total_stock_value', 0):,.2f}",
                "color": self.COLORS["secondary"],
                "icon": "💎"
            }
        ]

        # Draw metric cards (2x2 grid)
        card_width = (self.page_width - 2 * self.margin - 20) / 2
        card_height = 80

        for i, metric in enumerate(metrics):
            row = i // 2
            col = i % 2
            x = self.margin + col * (card_width + 20)
            y = y_pos + row * (card_height + 20)

            # Card background
            card_rect = fitz.Rect(x, y, x + card_width, y + card_height)
            page.draw_rect(card_rect, color=self._normalize_color(self.COLORS["light"]),
                          fill=self._normalize_color(self.COLORS["light"]))

            # Colored left border
            border_rect = fitz.Rect(x, y, x + 5, y + card_height)
            page.draw_rect(border_rect, color=self._normalize_color(metric["color"]),
                          fill=self._normalize_color(metric["color"]))

            # Icon
            self._insert_text(page, (x + 15, y + 30), metric["icon"], 24)

            # Label
            self._insert_text(page, (x + 50, y + 25), metric["label"], 10,
                           color=self._normalize_color(self.COLORS["text"]))

            # Value
            self._insert_text(page, (x + 50, y + 50), metric["value"], 18,
                           bold=True, color=self._normalize_color(metric["color"]))

        y_pos += 2 * (card_height + 20) + 30

        # Business information section
        y_pos = self._add_section_title(page, "Business Information", y_pos)

        info_items = [
            ("Shop Name", user_data.get("shop_name", "N/A")),
            ("Business Type", user_data.get("business_type", "N/A").replace("_", " ").title()),
            ("Owner", user_data.get("name", "N/A")),
            ("Phone", user_data.get("phone", "N/A")),
            ("Location", f"{user_data.get('location', {}).get('city', 'N/A')}, {user_data.get('location', {}).get('state', 'N/A')}"),
        ]

        for label, value in info_items:
            self._insert_text(page, (self.margin, y_pos), f"{label}:", 11,
                           bold=True, color=self._normalize_color(self.COLORS["secondary"]))
            self._insert_text(page, (self.margin + 150, y_pos), str(value), 11,
                           color=self._normalize_color(self.COLORS["text"]))
            y_pos += 25

        # Low stock alerts
        if analytics.get('low_stock_count', 0) > 0:
            y_pos += 20
            alert_rect = fitz.Rect(self.margin, y_pos, self.page_width - self.margin, y_pos + 50)
            page.draw_rect(alert_rect, color=self._normalize_color((255, 243, 224)),
                          fill=self._normalize_color((255, 243, 224)))

            self._insert_text(page, (self.margin + 10, y_pos + 20), "⚠️", 20)
            self._insert_text(page, (self.margin + 40, y_pos + 20), "Low Stock Alert", 12,
                           bold=True, color=self._normalize_color(self.COLORS["warning"]))
            self._insert_text(page, (self.margin + 40, y_pos + 38),
                           f"{analytics.get('low_stock_count', 0)} items need restocking",
                           10, color=self._normalize_color(self.COLORS["text"]))

        # Footer
        self._add_page_footer(page, 1)

    def _add_sales_page(self, doc: fitz.Document, sales_data: List[Dict[str, Any]], analytics: Dict[str, Any]):
        """Add sales analysis page"""
        page = doc.new_page(width=self.page_width, height=self.page_height)

        y_pos = self.margin

        # Header
        y_pos = self._add_page_header(page, "Sales Analysis", y_pos)
        y_pos += 20

        # Sales summary
        y_pos = self._add_section_title(page, "Recent Transactions", y_pos)

        # Table header
        headers = ["Date", "Type", "Items", "Amount", "Payment"]
        col_widths = [100, 80, 60, 90, 90]
        x_positions = [self.margin]
        for width in col_widths[:-1]:
            x_positions.append(x_positions[-1] + width)

        # Header background
        header_rect = fitz.Rect(self.margin, y_pos, self.page_width - self.margin, y_pos + 25)
        page.draw_rect(header_rect, color=self._normalize_color(self.COLORS["primary"]),
                      fill=self._normalize_color(self.COLORS["primary"]))

        # Header text
        for i, header in enumerate(headers):
            self._insert_text(page, (x_positions[i] + 5, y_pos + 17), header, 10,
                           bold=True, color=self._normalize_color(self.COLORS["white"]))

        y_pos += 25

        # Table rows (show last 10 transactions)
        recent_sales = sales_data[:10] if len(sales_data) > 10 else sales_data

        for idx, sale in enumerate(recent_sales):
            if y_pos > self.page_height - 100:
                break

            # Alternating row colors
            if idx % 2 == 0:
                row_rect = fitz.Rect(self.margin, y_pos, self.page_width - self.margin, y_pos + 22)
                page.draw_rect(row_rect, color=self._normalize_color((249, 249, 249)),
                              fill=self._normalize_color((249, 249, 249)))

            # Row data
            date_str = sale.get('timestamp', datetime.now()).strftime("%d %b %Y") if isinstance(sale.get('timestamp'), datetime) else "N/A"
            trans_type = sale.get('transaction_type', 'sale').upper()
            items_count = len(sale.get('items', []))
            amount = f"₹{sale.get('total_amount', 0):,.2f}"
            payment = sale.get('payment_mode', 'cash').title()

            row_data = [date_str, trans_type, str(items_count), amount, payment]

            for i, data in enumerate(row_data):
                self._insert_text(page, (x_positions[i] + 5, y_pos + 15), data, 9,
                               color=self._normalize_color(self.COLORS["text"]))

            y_pos += 22

        # Footer
        self._add_page_footer(page, 2)

    def _add_stock_page(self, doc: fitz.Document, stock_data: List[Dict[str, Any]], analytics: Dict[str, Any]):
        """Add stock analysis page"""
        page = doc.new_page(width=self.page_width, height=self.page_height)

        y_pos = self.margin

        # Header
        y_pos = self._add_page_header(page, "Stock Analysis", y_pos)
        y_pos += 20

        # Stock summary
        y_pos = self._add_section_title(page, "Current Inventory", y_pos)

        # Table header
        headers = ["Item Name", "Quantity", "Unit Price", "Total Value", "Status"]
        col_widths = [150, 70, 80, 90, 70]
        x_positions = [self.margin]
        for width in col_widths[:-1]:
            x_positions.append(x_positions[-1] + width)

        # Header background
        header_rect = fitz.Rect(self.margin, y_pos, self.page_width - self.margin, y_pos + 25)
        page.draw_rect(header_rect, color=self._normalize_color(self.COLORS["secondary"]),
                      fill=self._normalize_color(self.COLORS["secondary"]))

        # Header text
        for i, header in enumerate(headers):
            self._insert_text(page, (x_positions[i] + 5, y_pos + 17), header, 10,
                           bold=True, color=self._normalize_color(self.COLORS["white"]))

        y_pos += 25

        # Sort stock by value (highest first)
        sorted_stock = sorted(stock_data, key=lambda x: x.get('quantity', 0) * x.get('price_per_unit', 0), reverse=True)

        # Table rows (show top 15 items)
        top_stock = sorted_stock[:15] if len(sorted_stock) > 15 else sorted_stock

        for idx, item in enumerate(top_stock):
            if y_pos > self.page_height - 100:
                break

            # Alternating row colors
            if idx % 2 == 0:
                row_rect = fitz.Rect(self.margin, y_pos, self.page_width - self.margin, y_pos + 22)
                page.draw_rect(row_rect, color=self._normalize_color((249, 249, 249)),
                              fill=self._normalize_color((249, 249, 249)))

            # Row data
            item_name = item.get('item_name', 'N/A')[:25]  # Truncate long names
            quantity = item.get('quantity', 0)
            price = f"₹{item.get('price_per_unit', 0):,.2f}"
            total_value = f"₹{quantity * item.get('price_per_unit', 0):,.2f}"

            # Status based on quantity
            min_stock = item.get('min_stock_level', 10)
            if quantity == 0:
                status = "Out"
                status_color = self.COLORS["danger"]
            elif quantity <= min_stock:
                status = "Low"
                status_color = self.COLORS["warning"]
            else:
                status = "OK"
                status_color = self.COLORS["success"]

            row_data = [item_name, str(quantity), price, total_value]

            for i, data in enumerate(row_data):
                self._insert_text(page, (x_positions[i] + 5, y_pos + 15), data, 9,
                               color=self._normalize_color(self.COLORS["text"]))

            # Status with color
            self._insert_text(page, (x_positions[4] + 5, y_pos + 15), status, 9,
                           bold=True, color=self._normalize_color(status_color))

            y_pos += 22

        # Footer
        self._add_page_footer(page, 3)

    def _add_charts_page(self, doc: fitz.Document, sales_data: List[Dict[str, Any]], analytics: Dict[str, Any]):
        """Add charts and graphs page"""
        page = doc.new_page(width=self.page_width, height=self.page_height)

        y_pos = self.margin

        # Header
        y_pos = self._add_page_header(page, "Visual Analytics", y_pos)
        y_pos += 20

        # Sales trend chart (simple bar chart)
        y_pos = self._add_section_title(page, "7-Day Sales Trend", y_pos)

        # Calculate daily sales for last 7 days
        daily_sales = self._calculate_daily_sales(sales_data)

        # Draw bar chart
        chart_height = 150
        chart_width = self.page_width - 2 * self.margin - 60
        bar_width = chart_width / 7
        max_sale = max([s['amount'] for s in daily_sales]) if daily_sales else 1

        # Chart area
        chart_rect = fitz.Rect(self.margin + 50, y_pos, self.page_width - self.margin, y_pos + chart_height)
        page.draw_rect(chart_rect, color=self._normalize_color((245, 245, 245)),
                      fill=self._normalize_color((245, 245, 245)))

        # Draw bars
        for i, day_data in enumerate(daily_sales):
            bar_height = (day_data['amount'] / max_sale) * (chart_height - 30) if max_sale > 0 else 0
            bar_x = self.margin + 50 + i * bar_width + 5
            bar_y = y_pos + chart_height - bar_height - 20

            # Bar
            bar_rect = fitz.Rect(bar_x, bar_y, bar_x + bar_width - 10, y_pos + chart_height - 20)
            page.draw_rect(bar_rect, color=self._normalize_color(self.COLORS["primary"]),
                          fill=self._normalize_color(self.COLORS["primary"]))

            # Day label
            self._insert_text(page, (bar_x, y_pos + chart_height - 5), day_data['day'][:3],
                           8, color=self._normalize_color(self.COLORS["text"]))

            # Amount label
            if bar_height > 20:
                amount_text = f"₹{day_data['amount']:.0f}"
                self._insert_text(page, (bar_x, bar_y - 5), amount_text, 7,
                               color=self._normalize_color(self.COLORS["text"]))

        y_pos += chart_height + 40

        # Payment mode distribution (pie chart representation)
        y_pos = self._add_section_title(page, "Payment Mode Distribution", y_pos)

        payment_stats = self._calculate_payment_distribution(sales_data)

        # Draw simple pie chart representation as horizontal bars
        total_transactions = sum([p['count'] for p in payment_stats])

        for payment in payment_stats:
            if total_transactions == 0:
                break

            percentage = (payment['count'] / total_transactions) * 100
            bar_width_pct = (self.page_width - 2 * self.margin - 150) * (percentage / 100)

            # Payment mode label
            self._insert_text(page, (self.margin, y_pos + 15), payment['mode'].title(), 10,
                           color=self._normalize_color(self.COLORS["text"]))

            # Bar
            bar_rect = fitz.Rect(self.margin + 100, y_pos + 5, self.margin + 100 + bar_width_pct, y_pos + 20)
            color = self.COLORS["success"] if payment['mode'] == 'cash' else self.COLORS["primary"]
            page.draw_rect(bar_rect, color=self._normalize_color(color), fill=self._normalize_color(color))

            # Percentage label
            self._insert_text(page, (self.margin + 100 + bar_width_pct + 10, y_pos + 15),
                           f"{percentage:.1f}% ({payment['count']})", 9,
                           color=self._normalize_color(self.COLORS["text"]))

            y_pos += 30

        # Footer
        self._add_page_footer(page, 4)

    # Helper methods

    def _add_page_header(self, page: fitz.Page, title: str, y_pos: float) -> float:
        """Add page header with title"""
        # Title
        self._insert_text(page, (self.margin, y_pos + 20), title, 20,
                       bold=True, color=self._normalize_color(self.COLORS["primary"]))

        # Underline
        line_y = y_pos + 25
        page.draw_line(
            (self.margin, line_y),
            (self.page_width - self.margin, line_y),
            color=self._normalize_color(self.COLORS["primary"]),
            width=2
        )

        return y_pos + 35

    def _add_section_title(self, page: fitz.Page, title: str, y_pos: float) -> float:
        """Add section title"""
        self._insert_text(page, (self.margin, y_pos + 15), title, 14,
                       bold=True, color=self._normalize_color(self.COLORS["secondary"]))
        return y_pos + 25

    def _add_page_footer(self, page: fitz.Page, page_num: int):
        """Add page footer with page number"""
        footer_y = self.page_height - 30

        # Page number
        self._insert_text(page, (self.page_width / 2 - 10, footer_y), f"Page {page_num}",
                       9, color=self._normalize_color(self.COLORS["text"]))

        # Generated by Hisaab
        self._insert_text(page, (self.margin, footer_y), "Generated by Hisaab AI",
                       8, color=self._normalize_color(self.COLORS["text"]))

        # Date
        date_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
        self._insert_text(page, (self.page_width - self.margin - 100, footer_y), date_str,
                       8, color=self._normalize_color(self.COLORS["text"]))

    def _calculate_daily_sales(self, sales_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate daily sales for the last 7 days"""
        daily_totals = {}

        # Initialize last 7 days
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            day_key = date.strftime("%Y-%m-%d")
            daily_totals[day_key] = {
                'day': date.strftime("%A"),
                'date': day_key,
                'amount': 0,
                'count': 0
            }

        # Aggregate sales
        for sale in sales_data:
            timestamp = sale.get('timestamp')
            if isinstance(timestamp, datetime):
                day_key = timestamp.strftime("%Y-%m-%d")
                if day_key in daily_totals:
                    daily_totals[day_key]['amount'] += sale.get('total_amount', 0)
                    daily_totals[day_key]['count'] += 1

        return list(daily_totals.values())

    def _calculate_payment_distribution(self, sales_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate payment mode distribution"""
        payment_counts = {}

        for sale in sales_data:
            mode = sale.get('payment_mode', 'cash')
            if mode not in payment_counts:
                payment_counts[mode] = {'mode': mode, 'count': 0, 'amount': 0}
            payment_counts[mode]['count'] += 1
            payment_counts[mode]['amount'] += sale.get('total_amount', 0)

        return list(payment_counts.values())

