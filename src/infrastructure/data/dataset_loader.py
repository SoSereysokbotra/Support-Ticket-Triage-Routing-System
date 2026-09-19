import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from src.domain.entities.category import TicketCategory, TicketUrgency


class DatasetLoader:
    """
    Handles loading, bootstrapping, cleaning, and splitting ticket triage datasets.
    """

    DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

    SAMPLE_TEMPLATES: Dict[TicketCategory, List[str]] = {
        TicketCategory.HARDWARE: [
            "My laptop screen is flickering constantly and going black when I move the hinge.",
            "Dell desktop power button flashes amber and the PC won't power on at all.",
            "The external keyboard spacebar is stuck and typing multiple spaces.",
            "Printer on floor 3 is showing Paper Jam error even though the tray is completely empty.",
            "MacBook battery draining from 100% to 0% in 20 minutes. Battery status says Service Recommended.",
            "Docking station HDMI port stopped detecting the second monitor today.",
            "Office headset microphone is producing loud static noise on all Zoom calls.",
            "Mouse optical sensor is lagging and unresponsive across multiple USB ports.",
            "Server room UPS unit is beeping continuously with red battery replacement LED.",
            "Company iPad screen cracked after dropping from desk, touch is not responding.",
        ],
        TicketCategory.SOFTWARE: [
            "Excel crashes immediately whenever I try to open files with macros enabled.",
            "Outlook search bar is not returning any emails from the past two weeks.",
            "VS Code extension for Python keeps throwing language server initialization failed error.",
            "Adobe Acrobat DC gives error 0x80004005 when trying to digitally sign PDF invoices.",
            "Docker desktop fails to start the daemon engine after the recent Windows update.",
            "Chrome browser constantly runs out of memory and crashes tabs during analytics runs.",
            "ERP client freezes on the sales order generation screen after clicking Submit.",
            "Slack desktop application does not display notifications even when all settings are on.",
            "IntelliJ IDEA indexing is stuck at 99% and consuming 100% CPU.",
            "Internal CRM web portal throws 500 Internal Server Error when querying customer records.",
        ],
        TicketCategory.NETWORK: [
            "Cannot connect to the office Wi-Fi 'Corporate-Secure' - keeps prompting for credentials.",
            "VPN connection drops every 5 minutes with error: TLS handshake failed.",
            "Extremely slow internet speeds in Meeting Room B during video conferences.",
            "Cannot resolve internal domain dev.company.local - DNS lookup failure.",
            "Guest network SSID is not visible on mobile devices in the lobby area.",
            "Network shared drive Z: is disconnected and throws path not found error 0x80070035.",
            "Packet loss of 40% when pinging internal gateway router 10.0.0.1.",
            "Direct IP connection to staging database server times out on port 5432.",
            "Ethernet port on wall outlet #42 at desk 12 has no link light.",
            "Firewall is blocking outbound HTTPS traffic to our third-party API webhook.",
        ],
        TicketCategory.ACCESS_SECURITY: [
            "Locked out of Active Directory account after entering wrong password 3 times.",
            "Need MFA token reset for new iPhone because old phone was wiped.",
            "Requesting read-write permissions to Google Cloud Storage bucket finance-reports-prod.",
            "Received a suspicious phishing email claiming to be from CEO asking for gift cards.",
            "New employee onboarding: please provision Okta SSO account and Slack access for John Doe.",
            "GitHub organization invite expired, need access to repository mobile-app-v2.",
            "Password expiration warning: unable to change password through self-service portal.",
            "Need temporary SSH bastion host access to inspect production logs.",
            "Revoke all system access immediately for offboarding contractor Jane Smith.",
            "BitLocker recovery key prompt appeared on boot after BIOS update.",
        ],
        TicketCategory.BILLING_ADMIN: [
            "Invoice #INV-2026-9812 has an incorrect tax calculation for California entity.",
            "Need a copy of last month's AWS cloud infrastructure billing statement with itemized breakdown.",
            "Client was double-charged on their recurring monthly SaaS subscription.",
            "Update billing credit card information for corporate Zoom and Jira enterprise licenses.",
            "Vendor purchase order PO-88319 approved by manager, pending procurement sign-off.",
            "Expense report reimbursement stuck in pending approval status for 3 weeks.",
            "Requesting refund for unused seat licenses downgraded last billing cycle.",
            "Customer requesting W-9 form and bank ACH remittance details for wire transfer.",
            "Annual contract renewal discount terms need confirmation from finance director.",
            "Discrepancy in monthly Stripe transaction fees vs accounting ledger report.",
        ],
        TicketCategory.OTHER: [
            "Where can I find the updated company holiday schedule for Q3 and Q4?",
            "Lost building access keycard in the cafeteria yesterday afternoon.",
            "Requesting ergonomic chair and standing desk adjustment for desk B-14.",
            "General inquiry: What is the official process for submitting a patent disclosure?",
            "Feedback regarding cafeteria catering options for dietary restrictions.",
            "Lost and found: left umbrella near 4th floor reception desk.",
            "Requesting parking permit pass for visiting client next Tuesday.",
            "Inquiry regarding employee referral bonus payout timeline.",
            "Office temperature on 2nd floor is too cold throughout the afternoon.",
            "Update emergency contact information in HR portal directory.",
        ],
    }

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or self.DEFAULT_DATA_DIR
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def generate_bootstrap_dataset(
        self,
        num_samples: int = 1200,
        random_state: int = 42,
    ) -> pd.DataFrame:
        """
        Generates a realistic support ticket dataset with realistic class imbalance
        and varied text modifications for robust baseline model training.
        """
        random.seed(random_state)
        # Realistic class imbalance weights:
        # Software & Hardware dominate IT tickets; Billing & Other are smaller
        class_weights = {
            TicketCategory.SOFTWARE: 0.32,
            TicketCategory.HARDWARE: 0.25,
            TicketCategory.ACCESS_SECURITY: 0.18,
            TicketCategory.NETWORK: 0.13,
            TicketCategory.BILLING_ADMIN: 0.08,
            TicketCategory.OTHER: 0.04,
        }

        urgency_choices = [
            TicketUrgency.LOW,
            TicketUrgency.MEDIUM,
            TicketUrgency.HIGH,
            TicketUrgency.CRITICAL,
        ]
        urgency_weights = [0.25, 0.45, 0.20, 0.10]

        prefixes = [
            "Urgent: ",
            "Issue: ",
            "Problem report: ",
            "Help needed: ",
            "Fwd: Ticket - ",
            "Request: ",
            "",
            "CRITICAL: ",
            "[Support] ",
        ]

        suffixes = [
            " Please advise ASAP.",
            " Happening since this morning.",
            " Blocking my daily work.",
            " Thanks in advance.",
            " Any help would be appreciated.",
            " Already tried restarting with no luck.",
            "",
            " Need resolution before EOD.",
        ]

        records = []
        for _ in range(num_samples):
            # Sample category based on realistic weights
            cat = random.choices(
                list(class_weights.keys()),
                weights=list(class_weights.values()),
                k=1,
            )[0]

            base_text = random.choice(self.SAMPLE_TEMPLATES[cat])
            prefix = random.choice(prefixes)
            suffix = random.choice(suffixes)
            ticket_text = f"{prefix}{base_text}{suffix}".strip()

            urgency = random.choices(urgency_choices, weights=urgency_weights, k=1)[0]
            customer_id = f"CUST-{random.randint(1000, 9999)}"

            records.append({
                "text": ticket_text,
                "category": cat.value,
                "urgency": urgency.value,
                "customer_id": customer_id,
            })

        df = pd.DataFrame(records)
        raw_csv = self.raw_dir / "tickets_bootstrap.csv"
        df.to_csv(raw_csv, index=False)
        return df

    def load_or_create_dataset(
        self,
        csv_filename: Optional[str] = None,
        num_samples: Optional[int] = None,
        random_state: int = 42,
    ) -> pd.DataFrame:
        """
        Loads an existing dataset from raw directory, or generates a bootstrap dataset.
        """
        if csv_filename:
            path = self.raw_dir / csv_filename
            if path.exists():
                return pd.read_csv(path)

        if num_samples is not None:
            return self.generate_bootstrap_dataset(num_samples=num_samples, random_state=random_state)

        # Check if any CSV exists in raw_dir
        existing_csvs = list(self.raw_dir.glob("*.csv"))
        if existing_csvs:
            return pd.read_csv(existing_csvs[0])

        # Generate bootstrap
        return self.generate_bootstrap_dataset(random_state=random_state)

    def get_stratified_splits(
        self,
        df: Optional[pd.DataFrame] = None,
        test_size: float = 0.15,
        val_size: float = 0.15,
        random_state: int = 42,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Returns stratified (train, val, test) DataFrames based on category.
        """
        if df is None:
            df = self.load_or_create_dataset()

        # Clean invalid or empty texts
        df = df.dropna(subset=["text", "category"]).copy()
        df["text"] = df["text"].astype(str).str.strip()
        df = df[df["text"].str.len() >= 5]

        # First split: train+val vs test
        train_val_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=df["category"],
        )

        # Second split: train vs val
        relative_val_size = val_size / (1.0 - test_size)
        train_df, val_df = train_test_split(
            train_val_df,
            test_size=relative_val_size,
            random_state=random_state,
            stratify=train_val_df["category"],
        )

        # Save processed splits
        train_df.to_csv(self.processed_dir / "train.csv", index=False)
        val_df.to_csv(self.processed_dir / "val.csv", index=False)
        test_df.to_csv(self.processed_dir / "test.csv", index=False)

        return train_df, val_df, test_df

    def stratified_split(
        self,
        df: Optional[pd.DataFrame] = None,
        test_size: float = 0.15,
        val_size: float = 0.15,
        random_state: int = 42,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Alias for get_stratified_splits."""
        return self.get_stratified_splits(
            df=df,
            test_size=test_size,
            val_size=val_size,
            random_state=random_state,
        )
