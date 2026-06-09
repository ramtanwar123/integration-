import subprocess
import sys
import os
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--partner", required=True,
                        help="Partner name, e.g. alea_sgs, rootz")
    parser.add_argument("--html", action="store_true",
                        help="Generate HTML report")
    parser.add_argument("--base-url",
                        help="Override BASE_URL in config")
    args = parser.parse_args()

    partner = args.partner
    test_path = f"partners/{partner}/tests/"

    if not os.path.exists(test_path):
        print(f"Partner '{partner}' not found at {test_path}")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v",
        "--tb=short",
    ]

    if args.html:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        report_path = f"reports/{partner}_{timestamp}.html"
        os.makedirs("reports", exist_ok=True)
        cmd += [f"--html={report_path}", "--self-contained-html"]
        print(f"Report will be saved to: {report_path}")

    print(f"\nRunning tests for partner: {partner}")
    print("=" * 50)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()