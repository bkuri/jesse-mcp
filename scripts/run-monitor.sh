#!/bin/bash
set -e

NTFY_URL="${NTFY_URL:-https://ntfy.kuri.casa}"
NTFY_TOPIC="${NTFY_TOPIC:-jesse}"
NTFY_TOKEN="${NTFY_TOKEN:-tk_1vk4maedoxiw0kk66tbi8esfha8hc}"
SYMBOLS="${SYMBOLS:-BTC-USDT,ETH-USDT,SOL-USDT}"

MODE="${1:---scan}"

show_help() {
    cat << 'EOF'
Jesse MCP Monitor - Daily market scanning and alerting

Usage: run-monitor.sh [OPTIONS]

Options:
    --scan       Run daily market scan and alert on opportunities (default)
    --summary    Generate and send daily summary report
    --help       Show this help message

Environment Variables:
    NTFY_URL     ntfy server URL (default: https://ntfy.kuri.casa)
    NTFY_TOPIC   ntfy topic (default: jesse)
    NTFY_TOKEN   ntfy authentication token
    SYMBOLS      Comma-separated list of symbols to scan (default: BTC-USDT,ETH-USDT,SOL-USDT)

Examples:
    run-monitor.sh --scan
    run-monitor.sh --summary
    SYMBOLS=BTC-USDT,ETH-USDT run-monitor.sh --scan
EOF
}

if [ "$MODE" = "--help" ] || [ "$MODE" = "-h" ]; then
    show_help
    exit 0
fi

export NTFY_URL NTFY_TOPIC NTFY_TOKEN

python3 << PYTHON_SCRIPT
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("jesse-monitor")

def run_scan():
    """Run daily market scan and alert on opportunities"""
    from jesse_mcp.monitoring import MarketMonitor
    from jesse_mcp.alerts import send_ntfy_alert

    symbols_str = os.environ.get("SYMBOLS", "BTC-USDT,ETH-USDT,SOL-USDT")
    symbols = [s.strip() for s in symbols_str.split(",") if s.strip()]

    logger.info(f"Starting daily scan for symbols: {symbols}")

    monitor = MarketMonitor(symbols=symbols)
    report = monitor.daily_scan()

    opportunities = report.opportunities
    fg_score = report.fear_greed.get("score", 50)
    fg_rating = report.fear_greed.get("rating", "neutral")
    risks = report.risks

    logger.info(f"Scan complete: {len(opportunities)} opportunities, F&G: {fg_score}")

    if opportunities:
        top_opp = opportunities[0]
        message = (
            f"🎯 Trading Opportunities Detected\n\n"
            f"**{len(opportunities)} opportunities found**\n\n"
            f"Top Signal:\n"
            f"- Symbol: {top_opp['symbol']}\n"
            f"- Strategy: {top_opp['strategy']}\n"
            f"- Signal: {top_opp['signal'].upper()}\n"
            f"- Confidence: {top_opp['confidence']:.0%}\n"
            f"- Timeframe: {top_opp['timeframe']}\n\n"
            f"Market Context:\n"
            f"- Fear & Greed: {fg_score} ({fg_rating})\n"
        )

        if risks:
            message += f"\n⚠️ Risks:\n"
            for risk in risks[:3]:
                message += f"- {risk}\n"

        priority = "high" if len(opportunities) >= 3 else "default"
        tags = ["trading", "opportunity", "daily-scan"]

        result = send_ntfy_alert(
            message,
            priority=priority,
            tags=tags,
            title=f"Jesse: {len(opportunities)} Opportunities"
        )

        if result.get("success"):
            logger.info("Opportunity alert sent successfully")
        else:
            logger.error(f"Failed to send alert: {result.get('error')}")
            sys.exit(1)
    else:
        logger.info("No trading opportunities found")
        message = (
            f"📊 Daily Scan Complete\n\n"
            f"No trading opportunities detected.\n\n"
            f"Market Context:\n"
            f"- Fear & Greed: {fg_score} ({fg_rating})\n"
            f"- Risks: {len(risks)}\n"
        )

        if report.recommendations:
            message += f"\nRecommendations:\n"
            for rec in report.recommendations[:3]:
                message += f"- {rec}\n"

        send_ntfy_alert(
            message,
            priority="low",
            tags=["daily-scan", "no-opportunities"],
            title="Jesse: No Opportunities"
        )

def run_summary():
    """Generate and send daily summary report"""
    from jesse_mcp.logs import generate_weekly_report
    from jesse_mcp.alerts import send_daily_summary

    logger.info("Generating daily summary report...")

    report = generate_weekly_report()

    result = send_daily_summary(report, priority="default")

    if result.get("success"):
        logger.info("Daily summary sent successfully")
    else:
        logger.error(f"Failed to send summary: {result.get('error')}")
        sys.exit(1)

def main():
    mode = "${MODE}"

    try:
        if mode == "--scan":
            run_scan()
        elif mode == "--summary":
            run_summary()
        else:
            logger.error(f"Unknown mode: {mode}")
            sys.exit(1)
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Monitor failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
PYTHON_SCRIPT
