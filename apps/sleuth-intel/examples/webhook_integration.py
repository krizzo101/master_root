#!/usr/bin/env python3
"""
Webhook Integration Example
===========================

This example demonstrates how to integrate sleuth-intel with webhooks
for real-time notifications and event-driven workflows.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Install additional dependencies: pip install aiohttp fastapi uvicorn
3. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD
   - WEBHOOK_SECRET (optional, for security)

Usage:
------
python webhook_integration.py
"""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sleuth_intel import SleuthIntel
from sleuth_intel.models import (
    EmailVerificationRequest,
    PersonSearchRequest,
    PhoneLookupRequest,
)


class WebhookEvent(Enum):
    """Webhook event types."""

    SEARCH_COMPLETED = "search.completed"
    SEARCH_FAILED = "search.failed"
    VERIFICATION_COMPLETED = "verification.completed"
    VERIFICATION_FAILED = "verification.failed"
    ALERT_TRIGGERED = "alert.triggered"
    BATCH_COMPLETED = "batch.completed"
    BATCH_FAILED = "batch.failed"


class WebhookClient:
    """Client for sending webhook notifications."""

    def __init__(
        self,
        webhook_url: str,
        secret: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.webhook_url = webhook_url
        self.secret = secret
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def send_event(
        self,
        event_type: WebhookEvent,
        data: Dict[str, Any],
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Send webhook event.

        Args:
            event_type: Type of event
            data: Event data payload
            metadata: Optional metadata

        Returns:
            Success status
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        payload = {
            "event": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "metadata": metadata or {},
        }

        headers = {"Content-Type": "application/json", "X-Event-Type": event_type.value}

        # Add signature if secret is configured
        if self.secret:
            signature = self._generate_signature(payload)
            headers["X-Webhook-Signature"] = signature

        # Attempt to send with retries
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status in [200, 201, 202, 204]:
                        print(f"✅ Webhook sent successfully: {event_type.value}")
                        return True
                    else:
                        print(f"⚠️ Webhook failed with status {response.status}")

            except asyncio.TimeoutError:
                print(f"⏱️ Webhook timeout (attempt {attempt + 1}/{self.max_retries})")
            except Exception as e:
                print(f"❌ Webhook error: {str(e)}")

            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff

        return False

    def _generate_signature(self, payload: Dict) -> str:
        """Generate HMAC signature for webhook security."""
        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return signature


class WebhookIntegration:
    """Integration layer for sleuth-intel with webhooks."""

    def __init__(self, webhook_urls: List[str], secret: Optional[str] = None):
        self.client = SleuthIntel()
        self.webhook_clients = [WebhookClient(url, secret) for url in webhook_urls]
        self.active = True

    async def person_search_with_webhook(
        self, request_data: Dict[str, Any], callback_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform person search and send webhook on completion.

        Args:
            request_data: Person search parameters
            callback_id: Optional ID for tracking

        Returns:
            Search results
        """
        result = {
            "callback_id": callback_id
            or hashlib.sha256(f"{request_data}{datetime.now()}".encode()).hexdigest()[
                :12
            ],
            "status": "processing",
            "started_at": datetime.now().isoformat(),
        }

        try:
            # Perform search
            request = PersonSearchRequest(**request_data)
            response = await self.client.person_search(request)

            if response.success:
                result["status"] = "completed"
                result["data"] = {
                    "total_results": len(response.results),
                    "results": response.results[:10],  # Limit for webhook
                }

                # Send success webhook
                await self._send_webhooks(
                    WebhookEvent.SEARCH_COMPLETED, result, {"search_type": "person"}
                )
            else:
                result["status"] = "failed"
                result["error"] = response.error_message

                # Send failure webhook
                await self._send_webhooks(
                    WebhookEvent.SEARCH_FAILED, result, {"search_type": "person"}
                )

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

            await self._send_webhooks(
                WebhookEvent.SEARCH_FAILED,
                result,
                {"search_type": "person", "error_type": "exception"},
            )

        result["completed_at"] = datetime.now().isoformat()
        return result

    async def batch_verification_with_webhook(
        self,
        items: List[Dict[str, Any]],
        verification_type: str,
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform batch verification with webhook notifications.

        Args:
            items: List of items to verify
            verification_type: Type of verification (phone, email)
            batch_id: Optional batch ID

        Returns:
            Batch results
        """
        batch_id = (
            batch_id
            or hashlib.sha256(f"{len(items)}{datetime.now()}".encode()).hexdigest()[:12]
        )

        batch_result = {
            "batch_id": batch_id,
            "type": verification_type,
            "total_items": len(items),
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
            "started_at": datetime.now().isoformat(),
        }

        print(f"\n📦 Processing batch: {batch_id}")
        print(f"Items: {len(items)}")

        try:
            for i, item in enumerate(items):
                try:
                    if verification_type == "phone":
                        result = await self._verify_phone(item)
                    elif verification_type == "email":
                        result = await self._verify_email(item)
                    else:
                        result = {"error": f"Unknown type: {verification_type}"}

                    batch_result["results"].append(result)
                    batch_result["processed"] += 1

                    if result.get("success"):
                        batch_result["successful"] += 1
                    else:
                        batch_result["failed"] += 1

                    # Send progress webhook every 10 items
                    if (i + 1) % 10 == 0:
                        await self._send_progress_webhook(batch_result)

                except Exception as e:
                    batch_result["failed"] += 1
                    batch_result["results"].append({"input": item, "error": str(e)})

                # Rate limiting
                await asyncio.sleep(0.2)

            batch_result["completed_at"] = datetime.now().isoformat()
            batch_result["status"] = "completed"

            # Send completion webhook
            await self._send_webhooks(
                WebhookEvent.BATCH_COMPLETED,
                batch_result,
                {"verification_type": verification_type},
            )

        except Exception as e:
            batch_result["status"] = "failed"
            batch_result["error"] = str(e)

            await self._send_webhooks(
                WebhookEvent.BATCH_FAILED,
                batch_result,
                {"verification_type": verification_type},
            )

        return batch_result

    async def _verify_phone(self, phone_data: Dict) -> Dict[str, Any]:
        """Verify phone number."""
        try:
            request = PhoneLookupRequest(phone=phone_data.get("phone"))
            response = await self.client.phone_lookup(request)

            if response.success:
                return {
                    "input": phone_data,
                    "success": True,
                    "valid": response.is_valid,
                    "type": response.phone_type,
                    "carrier": response.carrier,
                }
            else:
                return {
                    "input": phone_data,
                    "success": False,
                    "error": response.error_message,
                }
        except Exception as e:
            return {"input": phone_data, "success": False, "error": str(e)}

    async def _verify_email(self, email_data: Dict) -> Dict[str, Any]:
        """Verify email address."""
        try:
            request = EmailVerificationRequest(email=email_data.get("email"))
            response = await self.client.email_verification(request)

            if response.success:
                return {
                    "input": email_data,
                    "success": True,
                    "valid": response.is_valid,
                    "deliverable": response.is_deliverable,
                    "disposable": response.is_disposable,
                }
            else:
                return {
                    "input": email_data,
                    "success": False,
                    "error": response.error_message,
                }
        except Exception as e:
            return {"input": email_data, "success": False, "error": str(e)}

    async def _send_webhooks(
        self,
        event_type: WebhookEvent,
        data: Dict[str, Any],
        metadata: Optional[Dict] = None,
    ):
        """Send webhooks to all configured endpoints."""
        tasks = []

        for client in self.webhook_clients:
            task = client.send_event(event_type, data, metadata)
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_progress_webhook(self, batch_result: Dict):
        """Send batch progress webhook."""
        progress_data = {
            "batch_id": batch_result["batch_id"],
            "processed": batch_result["processed"],
            "total": batch_result["total_items"],
            "progress_percent": (
                batch_result["processed"] / batch_result["total_items"] * 100
            ),
        }

        await self._send_webhooks(
            WebhookEvent.BATCH_COMPLETED, progress_data, {"type": "progress"}
        )

    async def close(self):
        """Clean up resources."""
        await self.client.close()
        for client in self.webhook_clients:
            if client.session:
                await client.session.close()


# Webhook receiver server example
app = FastAPI(title="Webhook Receiver Example")


@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Example webhook receiver endpoint.
    """
    # Verify signature if configured
    signature = request.headers.get("X-Webhook-Signature")
    if signature:
        # Verify signature logic here
        pass

    # Parse webhook data
    try:
        data = await request.json()
        event_type = data.get("event")
        timestamp = data.get("timestamp")
        payload = data.get("data")

        print(f"\n📨 Webhook received:")
        print(f"  Event: {event_type}")
        print(f"  Time: {timestamp}")

        # Process webhook based on event type
        if event_type == WebhookEvent.SEARCH_COMPLETED.value:
            background_tasks.add_task(process_search_completed, payload)
        elif event_type == WebhookEvent.VERIFICATION_COMPLETED.value:
            background_tasks.add_task(process_verification_completed, payload)
        elif event_type == WebhookEvent.BATCH_COMPLETED.value:
            background_tasks.add_task(process_batch_completed, payload)
        elif event_type == WebhookEvent.ALERT_TRIGGERED.value:
            background_tasks.add_task(process_alert, payload)

        return JSONResponse(
            content={"status": "received", "event": event_type}, status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def process_search_completed(data: Dict):
    """Process search completion webhook."""
    print(f"  Processing search results: {data.get('callback_id')}")
    # Add your processing logic here


async def process_verification_completed(data: Dict):
    """Process verification completion webhook."""
    print(f"  Processing verification: {data.get('callback_id')}")
    # Add your processing logic here


async def process_batch_completed(data: Dict):
    """Process batch completion webhook."""
    print(f"  Processing batch: {data.get('batch_id')}")
    print(f"  Successful: {data.get('successful')}/{data.get('total_items')}")
    # Add your processing logic here


async def process_alert(data: Dict):
    """Process alert webhook."""
    print(f"  ⚠️ Alert: {data.get('title')}")
    print(f"  Level: {data.get('level')}")
    # Add alert handling logic here


async def run_webhook_server():
    """Run the webhook receiver server."""
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Webhook Integration Example")
    print("=" * 60)

    # Start webhook receiver server in background
    print("\n🚀 Starting webhook receiver server on http://127.0.0.1:8000")
    server_task = asyncio.create_task(run_webhook_server())

    # Wait for server to start
    await asyncio.sleep(2)

    # Configure webhook integration
    webhook_urls = [
        "http://127.0.0.1:8000/webhook",
        # Add more webhook URLs as needed
    ]

    integration = WebhookIntegration(
        webhook_urls=webhook_urls, secret="your-webhook-secret"
    )

    # Example 1: Person search with webhook
    print("\n📌 Example 1: Person Search with Webhook")
    print("-" * 40)

    search_data = {
        "first_name": "John",
        "last_name": "Smith",
        "city": "Los Angeles",
        "state": "CA",
    }

    try:
        result = await integration.person_search_with_webhook(
            request_data=search_data, callback_id="SEARCH001"
        )

        print(f"✅ Search initiated: {result['callback_id']}")
        print(f"   Status: {result['status']}")

    except Exception as e:
        print(f"❌ Search failed: {str(e)}")

    # Example 2: Batch phone verification with webhook
    print("\n📌 Example 2: Batch Phone Verification with Webhook")
    print("-" * 40)

    phones = [
        {"phone": "5551234567"},
        {"phone": "5559876543"},
        {"phone": "5555551212"},
        {"phone": "5551112222"},
        {"phone": "5553334444"},
    ]

    try:
        batch_result = await integration.batch_verification_with_webhook(
            items=phones, verification_type="phone", batch_id="BATCH001"
        )

        print(f"✅ Batch completed: {batch_result['batch_id']}")
        print(
            f"   Processed: {batch_result['processed']}/{batch_result['total_items']}"
        )
        print(f"   Successful: {batch_result['successful']}")
        print(f"   Failed: {batch_result['failed']}")

    except Exception as e:
        print(f"❌ Batch failed: {str(e)}")

    # Example 3: Batch email verification with webhook
    print("\n📌 Example 3: Batch Email Verification with Webhook")
    print("-" * 40)

    emails = [
        {"email": "test1@example.com"},
        {"email": "test2@example.com"},
        {"email": "invalid@fake-domain.com"},
        {"email": "disposable@tempmail.com"},
    ]

    try:
        email_batch = await integration.batch_verification_with_webhook(
            items=emails, verification_type="email", batch_id="BATCH002"
        )

        print(f"✅ Email batch completed: {email_batch['batch_id']}")
        print(
            f"   Successful: {email_batch['successful']}/{email_batch['total_items']}"
        )

    except Exception as e:
        print(f"❌ Email batch failed: {str(e)}")

    # Clean up
    await integration.close()

    # Stop server
    print("\n🛑 Stopping webhook server...")
    server_task.cancel()

    print("\n✨ Webhook integration example completed!")


if __name__ == "__main__":
    asyncio.run(main())
