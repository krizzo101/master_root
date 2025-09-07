#!/usr/bin/env python3
"""
Bulk Processing Example
=======================

This example demonstrates high-volume bulk processing capabilities
with parallel execution, rate limiting, and progress tracking.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD

Usage:
------
python bulk_processing.py
"""

import asyncio
import csv
import json
import logging
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sleuth_intel import SleuthIntel
from sleuth_intel.models import (
    AddressSearchRequest,
    EmailVerificationRequest,
    PersonSearchRequest,
    PhoneLookupRequest,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BulkProcessor:
    """High-volume data processing engine."""

    def __init__(
        self,
        max_workers: int = 5,
        rate_limit: int = 10,  # requests per second
        batch_size: int = 100,
    ):
        self.client = SleuthIntel()
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self.batch_size = batch_size
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None
        self.results = []
        self.errors = []

    async def process_csv(
        self,
        input_file: str,
        operation: str,
        output_file: Optional[str] = None,
        resume_from: int = 0,
    ) -> Dict[str, Any]:
        """
        Process data from CSV file.

        Args:
            input_file: Path to input CSV file
            operation: Type of operation (person_search, phone_lookup, email_verify, address_verify)
            output_file: Optional output file path
            resume_from: Row number to resume from (for interrupted processing)

        Returns:
            Processing summary
        """
        print(f"\n📂 Bulk CSV Processing")
        print(f"Input: {input_file}")
        print(f"Operation: {operation}")
        print("=" * 60)

        self.start_time = time.time()

        # Read CSV file
        data = []
        with open(input_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= resume_from:
                    data.append(row)

        total_records = len(data)
        print(f"📊 Total records to process: {total_records}")
        if resume_from > 0:
            print(f"⏩ Resuming from row {resume_from}")

        # Process in batches
        for batch_num, batch_start in enumerate(
            range(0, total_records, self.batch_size)
        ):
            batch_end = min(batch_start + self.batch_size, total_records)
            batch = data[batch_start:batch_end]

            print(
                f"\n🔄 Processing batch {batch_num + 1} ({batch_start + 1}-{batch_end}/{total_records})"
            )

            # Process batch based on operation type
            if operation == "person_search":
                await self._process_person_batch(batch)
            elif operation == "phone_lookup":
                await self._process_phone_batch(batch)
            elif operation == "email_verify":
                await self._process_email_batch(batch)
            elif operation == "address_verify":
                await self._process_address_batch(batch)
            else:
                raise ValueError(f"Unknown operation: {operation}")

            # Show progress
            self._show_progress(batch_end, total_records)

            # Save intermediate results
            if batch_num % 5 == 0:
                self._save_checkpoint(output_file, batch_end + resume_from)

        # Generate final report
        summary = self._generate_summary(total_records)

        # Save final results
        if output_file:
            self._save_results(output_file, summary)

        return summary

    async def _process_person_batch(self, batch: List[Dict]):
        """Process batch of person searches."""
        tasks = []

        for record in batch:
            task = self._process_person(record)
            tasks.append(task)

            # Rate limiting
            if len(tasks) >= self.max_workers:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                self._handle_batch_results(results)
                tasks = []
                await asyncio.sleep(1 / self.rate_limit)

        # Process remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self._handle_batch_results(results)

    async def _process_person(self, record: Dict) -> Dict[str, Any]:
        """Process single person search."""
        try:
            request = PersonSearchRequest(
                first_name=record.get("first_name"),
                last_name=record.get("last_name"),
                middle_name=record.get("middle_name"),
                date_of_birth=record.get("date_of_birth"),
                ssn_last4=record.get("ssn_last4"),
                address=record.get("address"),
                city=record.get("city"),
                state=record.get("state"),
                zip_code=record.get("zip_code"),
            )

            response = await self.client.person_search(request)

            if response.success and response.results:
                top_match = response.results[0]
                return {
                    "input": record,
                    "success": True,
                    "match_found": True,
                    "result": {
                        "name": f"{top_match.get('first_name', '')} {top_match.get('last_name', '')}",
                        "age": top_match.get("age"),
                        "addresses": len(top_match.get("addresses", [])),
                        "phones": len(top_match.get("phones", [])),
                        "emails": len(top_match.get("emails", [])),
                        "confidence": top_match.get("match_confidence", 0),
                    },
                }
            else:
                return {
                    "input": record,
                    "success": True,
                    "match_found": False,
                    "result": None,
                }

        except Exception as e:
            logger.error(f"Error processing person: {e}")
            return {"input": record, "success": False, "error": str(e)}

    async def _process_phone_batch(self, batch: List[Dict]):
        """Process batch of phone lookups."""
        tasks = []

        for record in batch:
            task = self._process_phone(record)
            tasks.append(task)

            if len(tasks) >= self.max_workers:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                self._handle_batch_results(results)
                tasks = []
                await asyncio.sleep(1 / self.rate_limit)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self._handle_batch_results(results)

    async def _process_phone(self, record: Dict) -> Dict[str, Any]:
        """Process single phone lookup."""
        try:
            phone = (
                record.get("phone", "")
                .replace("-", "")
                .replace(" ", "")
                .replace("(", "")
                .replace(")", "")
            )

            request = PhoneLookupRequest(phone=phone)
            response = await self.client.phone_lookup(request)

            if response.success:
                return {
                    "input": record,
                    "success": True,
                    "result": {
                        "phone": response.phone_number,
                        "valid": response.is_valid,
                        "type": response.phone_type,
                        "carrier": response.carrier,
                        "owner": response.owner_info.get("name")
                        if response.owner_info
                        else None,
                        "location": f"{response.location_info.get('city', '')}, {response.location_info.get('state', '')}"
                        if response.location_info
                        else None,
                    },
                }
            else:
                return {
                    "input": record,
                    "success": False,
                    "error": response.error_message,
                }

        except Exception as e:
            logger.error(f"Error processing phone: {e}")
            return {"input": record, "success": False, "error": str(e)}

    async def _process_email_batch(self, batch: List[Dict]):
        """Process batch of email verifications."""
        tasks = []

        for record in batch:
            task = self._process_email(record)
            tasks.append(task)

            if len(tasks) >= self.max_workers:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                self._handle_batch_results(results)
                tasks = []
                await asyncio.sleep(1 / self.rate_limit)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self._handle_batch_results(results)

    async def _process_email(self, record: Dict) -> Dict[str, Any]:
        """Process single email verification."""
        try:
            email = record.get("email", "").strip().lower()

            request = EmailVerificationRequest(email=email)
            response = await self.client.email_verification(request)

            if response.success:
                return {
                    "input": record,
                    "success": True,
                    "result": {
                        "email": email,
                        "valid": response.is_valid,
                        "deliverable": response.is_deliverable,
                        "disposable": response.is_disposable,
                        "role_based": response.is_role_based,
                        "free_provider": response.is_free_provider,
                        "domain": response.domain,
                    },
                }
            else:
                return {
                    "input": record,
                    "success": False,
                    "error": response.error_message,
                }

        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return {"input": record, "success": False, "error": str(e)}

    async def _process_address_batch(self, batch: List[Dict]):
        """Process batch of address verifications."""
        tasks = []

        for record in batch:
            task = self._process_address(record)
            tasks.append(task)

            if len(tasks) >= self.max_workers:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                self._handle_batch_results(results)
                tasks = []
                await asyncio.sleep(1 / self.rate_limit)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self._handle_batch_results(results)

    async def _process_address(self, record: Dict) -> Dict[str, Any]:
        """Process single address verification."""
        try:
            request = AddressSearchRequest(
                address=record.get("address"),
                city=record.get("city"),
                state=record.get("state"),
                zip_code=record.get("zip_code"),
            )

            response = await self.client.address_search(request)

            if response.success:
                return {
                    "input": record,
                    "success": True,
                    "result": {
                        "formatted_address": response.formatted_address,
                        "valid": True,
                        "residential": response.is_residential,
                        "commercial": response.is_commercial,
                        "deliverable": response.is_deliverable,
                        "vacant": response.is_vacant,
                    },
                }
            else:
                return {
                    "input": record,
                    "success": False,
                    "error": response.error_message,
                }

        except Exception as e:
            logger.error(f"Error processing address: {e}")
            return {"input": record, "success": False, "error": str(e)}

    def _handle_batch_results(self, results: List):
        """Handle batch processing results."""
        for result in results:
            if isinstance(result, Exception):
                self.error_count += 1
                self.errors.append(str(result))
            elif isinstance(result, dict):
                self.processed_count += 1
                self.results.append(result)

                if not result.get("success"):
                    self.error_count += 1
                    self.errors.append(result.get("error", "Unknown error"))

    def _show_progress(self, current: int, total: int):
        """Display processing progress."""
        elapsed = time.time() - self.start_time
        rate = self.processed_count / elapsed if elapsed > 0 else 0
        eta = (total - current) / rate if rate > 0 else 0

        print(f"  ⏱️ Processed: {self.processed_count}/{total}")
        print(
            f"  📊 Success Rate: {((self.processed_count - self.error_count) / self.processed_count * 100) if self.processed_count > 0 else 0:.1f}%"
        )
        print(f"  🚀 Rate: {rate:.1f} records/sec")
        print(f"  ⏰ ETA: {timedelta(seconds=int(eta))}")

    def _save_checkpoint(self, output_file: Optional[str], row_number: int):
        """Save intermediate results checkpoint."""
        if not output_file:
            return

        checkpoint_file = f"{output_file}.checkpoint_{row_number}.json"
        with open(checkpoint_file, "w") as f:
            json.dump(
                {
                    "row_number": row_number,
                    "processed": self.processed_count,
                    "errors": self.error_count,
                    "results": self.results[-100:],  # Save last 100 results
                },
                f,
                indent=2,
            )

        logger.info(f"Checkpoint saved: {checkpoint_file}")

    def _generate_summary(self, total_records: int) -> Dict[str, Any]:
        """Generate processing summary."""
        elapsed = time.time() - self.start_time

        summary = {
            "total_records": total_records,
            "processed": self.processed_count,
            "successful": self.processed_count - self.error_count,
            "failed": self.error_count,
            "success_rate": (
                (self.processed_count - self.error_count) / self.processed_count * 100
            )
            if self.processed_count > 0
            else 0,
            "processing_time": str(timedelta(seconds=int(elapsed))),
            "average_rate": self.processed_count / elapsed if elapsed > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }

        print("\n" + "=" * 60)
        print("📊 PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total Records: {summary['total_records']}")
        print(f"Processed: {summary['processed']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Processing Time: {summary['processing_time']}")
        print(f"Average Rate: {summary['average_rate']:.1f} records/sec")

        return summary

    def _save_results(self, output_file: str, summary: Dict):
        """Save final results to file."""
        # Save detailed results as JSON
        json_file = f"{output_file}.json"
        with open(json_file, "w") as f:
            json.dump(
                {"summary": summary, "results": self.results, "errors": self.errors},
                f,
                indent=2,
            )

        # Save summary as CSV
        csv_file = f"{output_file}.csv"
        if self.results:
            with open(csv_file, "w", newline="") as f:
                # Flatten results for CSV
                flattened = []
                for r in self.results:
                    row = {**r.get("input", {})}
                    if r.get("result"):
                        for k, v in r["result"].items():
                            row[f"result_{k}"] = v
                    row["success"] = r.get("success", False)
                    if r.get("error"):
                        row["error"] = r["error"]
                    flattened.append(row)

                if flattened:
                    writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened)

        print(f"\n💾 Results saved:")
        print(f"  • JSON: {json_file}")
        print(f"  • CSV: {csv_file}")

    async def close(self):
        """Clean up resources."""
        await self.client.close()


class ParallelProcessor:
    """Parallel processing for maximum throughput."""

    def __init__(self, num_workers: int = 10):
        self.num_workers = num_workers
        self.processors = []
        self.queue = asyncio.Queue()
        self.results = []
        self.stats = defaultdict(int)

    async def process_mixed_batch(
        self, tasks: List[Dict[str, Any]], output_dir: str = "bulk_results"
    ) -> Dict[str, Any]:
        """
        Process mixed batch of different operation types in parallel.

        Args:
            tasks: List of task dictionaries with 'type' and 'data' keys
            output_dir: Directory for output files

        Returns:
            Processing summary
        """
        print(f"\n🚀 Parallel Mixed Batch Processing")
        print(f"Workers: {self.num_workers}")
        print(f"Total Tasks: {len(tasks)}")
        print("=" * 60)

        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)

        # Start workers
        workers = []
        for i in range(self.num_workers):
            processor = BulkProcessor(max_workers=1, rate_limit=5)
            self.processors.append(processor)
            worker = asyncio.create_task(self._worker(i, processor))
            workers.append(worker)

        # Add tasks to queue
        for task in tasks:
            await self.queue.put(task)

        # Add stop signals
        for _ in range(self.num_workers):
            await self.queue.put(None)

        # Wait for workers to complete
        await asyncio.gather(*workers)

        # Generate summary
        summary = {
            "total_tasks": len(tasks),
            "completed": self.stats["completed"],
            "failed": self.stats["failed"],
            "by_type": dict(self.stats),
            "timestamp": datetime.now().isoformat(),
        }

        # Save results
        summary_file = (
            f"{output_dir}/parallel_summary_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 60)
        print("📊 PARALLEL PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Total Tasks: {summary['total_tasks']}")
        print(f"Completed: {summary['completed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Results saved to: {output_dir}")

        # Clean up
        for processor in self.processors:
            await processor.close()

        return summary

    async def _worker(self, worker_id: int, processor: BulkProcessor):
        """Worker coroutine for parallel processing."""
        while True:
            task = await self.queue.get()

            if task is None:
                break

            try:
                task_type = task.get("type")
                data = task.get("data")

                logger.info(f"Worker {worker_id}: Processing {task_type}")

                if task_type == "person":
                    result = await processor._process_person(data)
                elif task_type == "phone":
                    result = await processor._process_phone(data)
                elif task_type == "email":
                    result = await processor._process_email(data)
                elif task_type == "address":
                    result = await processor._process_address(data)
                else:
                    result = {"error": f"Unknown task type: {task_type}"}

                self.results.append(result)

                if result.get("success"):
                    self.stats["completed"] += 1
                    self.stats[f"{task_type}_success"] += 1
                else:
                    self.stats["failed"] += 1
                    self.stats[f"{task_type}_failed"] += 1

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                self.stats["failed"] += 1


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Bulk Processing Example")
    print("=" * 60)

    # Example 1: Bulk CSV processing
    print("\n📌 Example 1: Bulk CSV Processing")
    print("-" * 40)

    # Create sample CSV file
    sample_csv = "sample_bulk_data.csv"
    with open(sample_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["first_name", "last_name", "city", "state"]
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "city": "Los Angeles",
                    "state": "CA",
                },
                {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "city": "New York",
                    "state": "NY",
                },
                {
                    "first_name": "Bob",
                    "last_name": "Johnson",
                    "city": "Chicago",
                    "state": "IL",
                },
                {
                    "first_name": "Alice",
                    "last_name": "Williams",
                    "city": "Houston",
                    "state": "TX",
                },
                {
                    "first_name": "Charlie",
                    "last_name": "Brown",
                    "city": "Phoenix",
                    "state": "AZ",
                },
            ]
        )

    processor = BulkProcessor(max_workers=3, rate_limit=5, batch_size=2)

    try:
        summary = await processor.process_csv(
            input_file=sample_csv,
            operation="person_search",
            output_file="bulk_person_results",
        )

        print("\n✅ Bulk processing completed!")

    except Exception as e:
        print(f"❌ Bulk processing failed: {str(e)}")

    finally:
        await processor.close()

    # Example 2: Parallel mixed processing
    print("\n📌 Example 2: Parallel Mixed Processing")
    print("-" * 40)

    # Create mixed tasks
    mixed_tasks = [
        {"type": "person", "data": {"first_name": "John", "last_name": "Smith"}},
        {"type": "phone", "data": {"phone": "5551234567"}},
        {"type": "email", "data": {"email": "test@example.com"}},
        {
            "type": "address",
            "data": {"address": "123 Main St", "city": "Los Angeles", "state": "CA"},
        },
        {"type": "person", "data": {"first_name": "Jane", "last_name": "Doe"}},
        {"type": "phone", "data": {"phone": "5559876543"}},
        {"type": "email", "data": {"email": "info@company.com"}},
        {
            "type": "address",
            "data": {"address": "456 Oak Ave", "city": "New York", "state": "NY"},
        },
    ]

    parallel_processor = ParallelProcessor(num_workers=4)

    try:
        summary = await parallel_processor.process_mixed_batch(
            tasks=mixed_tasks, output_dir="parallel_results"
        )

        print("\n✅ Parallel processing completed!")

    except Exception as e:
        print(f"❌ Parallel processing failed: {str(e)}")

    print("\n✨ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
