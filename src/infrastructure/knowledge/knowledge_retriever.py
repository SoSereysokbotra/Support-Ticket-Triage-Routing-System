"""
Enterprise Standard Operating Procedure (SOP) Knowledge Retriever (RAG Source).
Provides grounded, category-indexed resolution playbooks for Copilot draft generation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SOPArticle:
    """Standard Operating Procedure playbook document."""
    article_id: str
    title: str
    category: str
    summary: str
    keywords: List[str]
    resolution_steps: List[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "category": self.category,
            "summary": self.summary,
            "resolution_steps": self.resolution_steps,
        }


DEFAULT_SOP_DATABASE: List[SOPArticle] = [
    SOPArticle(
        article_id="SOP-NET-001",
        title="GlobalProtect & Cisco AnyConnect VPN Gateway Connection Drop Resolution",
        category="Network",
        summary="Resolves TLS handshake drops, stale tunnel virtual adapter routes, and VPN gateway resets.",
        keywords=["vpn", "handshake", "gateway", "tunnel", "anyconnect", "globalprotect", "disconnect"],
        resolution_steps=[
            "Open Command Prompt as Administrator and run 'ipconfig /flushdns'.",
            "Reset virtual network adapters by executing 'netsh winsock reset' and restarting the workstation.",
            "In your VPN client settings, switch connection gateway from 'Auto-Detect' to 'us-east-gw.corp.net'.",
            "Verify that local Wi-Fi router is not blocking IPsec/IKEv2 ports (UDP 500/4500).",
        ],
    ),
    SOPArticle(
        article_id="SOP-NET-002",
        title="Corporate DNS Cache Corruption & BGP Peering Route Flapping",
        category="Network",
        summary="Standard recovery protocol for internal domain name resolution failures and intranet timeouts.",
        keywords=["dns", "resolution", "timeout", "bgp", "domain", "intranet", "peering"],
        resolution_steps=[
            "Flush operating system DNS cache: 'ipconfig /flushdns'.",
            "Switch primary and secondary internal DNS to 10.0.0.53 and 10.0.0.54.",
            "Verify local hosts file ('C:\\Windows\\System32\\drivers\\etc\\hosts') has no stale intranet overrides.",
            "If persists, escalate to NOC team to check BGP route health on the regional core switch.",
        ],
    ),
    SOPArticle(
        article_id="SOP-SEC-001",
        title="Single Sign-On (Okta / Azure AD) Infinite Redirect Loop & SAML Error",
        category="Access & Security",
        summary="Fixes SAML token replay drops, clock skew errors, and browser SSO authentication loops.",
        keywords=["sso", "okta", "azure", "saml", "redirect", "login", "password", "auth", "token"],
        resolution_steps=[
            "Clear all browser session cookies and site data for '*.okta.com' and '*.microsoftonline.com'.",
            "Verify system clock synchronization under Date & Time settings (clock drift > 120s invalidates SAML tokens).",
            "Launch an incognito or private browsing window to bypass cached token exchange states.",
            "If account is locked due to repeated bad password attempts, request an unlock from IT Security Lead.",
        ],
    ),
    SOPArticle(
        article_id="SOP-SEC-002",
        title="MFA Hardware Token / Authenticator App Resynchronization",
        category="Access & Security",
        summary="Procedure for lost mobile authenticators, expired TOTP seeds, and backup passcode issuance.",
        keywords=["mfa", "totp", "authenticator", "yubikey", "token", "2fa", "code"],
        resolution_steps=[
            "Verify identity via secondary verified employee phone number or manager confirmation.",
            "Generate an emergency 24-hour bypass code from Okta Admin Console.",
            "Instruct user to revoke old authenticator profile under 'Security Settings'.",
            "Re-enroll user's new device via QR code registration while connected to the secure corporate portal.",
        ],
    ),
    SOPArticle(
        article_id="SOP-HW-001",
        title="DisplayPort Multi-Monitor Daisy-Chain Flickering & Black Screen Diagnostics",
        category="Hardware",
        summary="Troubleshooting steps for flickering external displays, HDMI/DisplayPort cable drops, and MST hubs.",
        keywords=["monitor", "screen", "flicker", "display", "black", "displayport", "hdmi", "cable"],
        resolution_steps=[
            "Reseat both ends of the DisplayPort/HDMI cable firmly and avoid passive adapter chains.",
            "Lower monitor refresh rate in Windows Display Settings from 144Hz to 60Hz to test bandwidth limits.",
            "Disable 'DisplayPort 1.2 MST' (Multi-Stream Transport) in the monitor's built-in OSD menu if using a single display.",
            "Update Intel/Nvidia graphics drivers to corporate certified version 536.99 or later.",
        ],
    ),
    SOPArticle(
        article_id="SOP-HW-002",
        title="Thunderbolt Docking Station Power Delivery & Peripheral Dropout Resolution",
        category="Hardware",
        summary="Resolves unrecognized USB peripherals, Ethernet port failures, and power delivery drops on docks.",
        keywords=["dock", "thunderbolt", "usb", "docking", "peripherals", "ethernet", "laptop"],
        resolution_steps=[
            "Perform a cold power cycle on the dock: disconnect laptop, unplug dock power cord, hold power button 15 seconds.",
            "Plug dock back into AC power before reconnecting the Thunderbolt cable to laptop.",
            "Verify Thunderbolt device authorization status in the Thunderbolt Control Center app.",
            "Apply firmware update v2.4.1 from the enterprise software center.",
        ],
    ),
    SOPArticle(
        article_id="SOP-BILL-001",
        title="Payment Gateway Timeout & Duplicate Invoice Reconciliation",
        category="Billing",
        summary="Standard handling for Stripe/Adyen credit card timeouts, pending auth holds, and double billing.",
        keywords=["billing", "invoice", "payment", "card", "charge", "refund", "receipt", "credit"],
        resolution_steps=[
            "Query payment gateway logs for the transaction idempotency key to confirm settlement status.",
            "If transaction is in 'authorized_pending' state, issue a void authorization to release customer bank hold.",
            "Re-issue zero-balance receipt once the primary transaction captures successfully.",
            "Attach the gateway reference ID to the accounting ledger ticket.",
        ],
    ),
    SOPArticle(
        article_id="SOP-SOFT-001",
        title="Docker Daemon Socket Failure ('docker.sock' Connection Refused) in WSL2",
        category="Software",
        summary="Resolves local container engine crashes, corrupted WSL2 distributions, and pipe permissions.",
        keywords=["docker", "daemon", "socket", "wsl", "container", "crash", "engine", "service"],
        resolution_steps=[
            "Open PowerShell as Administrator and restart WSL: 'wsl --shutdown'.",
            "Restart Docker Desktop service from Windows Services Manager ('services.msc').",
            "Verify in Docker Desktop Settings -> Resources -> WSL Integration that your distro is enabled.",
            "Check disk space on C:\\ drive (Docker crashes if free disk space is under 5GB).",
        ],
    ),
    SOPArticle(
        article_id="SOP-SOFT-002",
        title="Git SSH Key Authentication Failed ('Permission denied (publickey)')",
        category="Software",
        summary="Troubleshooting Git CLI SSH key permission errors and corporate GitHub/GitLab agent forwarding.",
        keywords=["git", "ssh", "key", "permission", "denied", "publickey", "github", "gitlab"],
        resolution_steps=[
            "Verify SSH agent is running: 'eval $(ssh-agent -s)' and add key: 'ssh-add ~/.ssh/id_ed25519'.",
            "Ensure SSH private key permissions are secure: 'chmod 600 ~/.ssh/id_ed25519'.",
            "Test remote handshake: 'ssh -Tv git@github.com' to view verbose negotiation logs.",
            "If key is not recognized, copy output of 'cat ~/.ssh/id_ed25519.pub' into corporate Git user keys.",
        ],
    ),
]


class KnowledgeRetriever:
    """
    In-memory semantic & keyword BM25-style playbook retriever.
    Extracts relevant Standard Operating Procedures matching ticket issues.
    """

    def __init__(self, database: Optional[List[SOPArticle]] = None) -> None:
        self._database = database if database is not None else DEFAULT_SOP_DATABASE

    @property
    def articles(self) -> List[SOPArticle]:
        """Returns the loaded list of SOP articles."""
        return self._database

    def find_relevant_sops(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 2,
        limit: Optional[int] = None,
    ) -> List[SOPArticle]:
        """
        Retrieves the top-k most relevant SOP playbooks for the given issue query.
        Scores by category alignment and token overlap in title, summary, and keywords.
        """
        if limit is not None:
            top_k = limit
        if not query and not category:
            return []

        # Tokenize query
        tokens = set(re.findall(r"[a-z0-9]+", (query or "").lower()))

        scored_articles: List[tuple[float, SOPArticle]] = []
        for article in self._database:
            score = 0.0

            # Strong category boost (exact or substring match)
            if category and (
                article.category.lower() == category.lower()
                or category.lower() in article.category.lower()
                or article.category.lower() in category.lower()
            ):
                score += 5.0

            # Keyword match boost
            for kw in article.keywords:
                if kw.lower() in tokens:
                    score += 3.0

            # Title token match
            title_tokens = set(re.findall(r"[a-z0-9]+", article.title.lower()))
            common_title = tokens.intersection(title_tokens)
            score += len(common_title) * 1.5

            # Summary token match
            summary_tokens = set(re.findall(r"[a-z0-9]+", article.summary.lower()))
            common_summary = tokens.intersection(summary_tokens)
            score += len(common_summary) * 0.5

            if score > 0.0:
                scored_articles.append((score, article))

        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [art for _, art in scored_articles[:top_k]]
