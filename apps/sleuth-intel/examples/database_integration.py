#!/usr/bin/env python3
"""
Database Integration Example
============================

This example demonstrates how to integrate sleuth-intel with databases
for persistent storage and batch processing.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Install database dependencies: pip install sqlalchemy asyncpg psycopg2-binary
3. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD
   - DATABASE_URL (e.g., postgresql://user:pass@localhost/dbname)

Usage:
------
python database_integration.py
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sleuth_intel import SleuthIntel
from sleuth_intel.models import (
    AddressSearchRequest,
    EmailVerificationRequest,
    PersonSearchRequest,
    PhoneLookupRequest,
)
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    and_,
    create_engine,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

Base = declarative_base()


# Database Models
class SearchRecord(Base):
    """Record of search operations."""

    __tablename__ = "search_records"

    id = Column(String(50), primary_key=True)
    search_type = Column(String(50), nullable=False)
    search_params = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False)
    result_count = Column(Integer, default=0)
    results = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processing_time = Column(Float)

    # Indexes
    __table_args__ = (
        Index("idx_search_type", "search_type"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
    )


class PersonRecord(Base):
    """Person information records."""

    __tablename__ = "person_records"

    id = Column(String(50), primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    date_of_birth = Column(String(20))
    age = Column(Integer)
    ssn_last4 = Column(String(4))

    # Contact information
    phones = Column(JSON)
    emails = Column(JSON)
    addresses = Column(JSON)

    # Relationships
    relatives = Column(JSON)
    associates = Column(JSON)

    # Metadata
    confidence_score = Column(Float)
    last_verified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Related verifications
    verifications = relationship("VerificationRecord", back_populates="person")

    __table_args__ = (
        Index("idx_person_name", "first_name", "last_name"),
        Index("idx_person_dob", "date_of_birth"),
    )


class VerificationRecord(Base):
    """Verification history records."""

    __tablename__ = "verification_records"

    id = Column(String(50), primary_key=True)
    person_id = Column(String(50), ForeignKey("person_records.id"))
    verification_type = Column(String(50), nullable=False)
    verification_data = Column(JSON, nullable=False)

    # Results
    is_valid = Column(Boolean)
    confidence_score = Column(Float)
    risk_score = Column(Integer)
    risk_factors = Column(JSON)

    # Metadata
    performed_at = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float)

    # Relationship
    person = relationship("PersonRecord", back_populates="verifications")

    __table_args__ = (
        Index("idx_verification_type", "verification_type"),
        Index("idx_performed_at", "performed_at"),
    )


class PhoneRecord(Base):
    """Phone number records."""

    __tablename__ = "phone_records"

    phone_number = Column(String(20), primary_key=True)
    phone_type = Column(String(50))
    carrier = Column(String(100))
    line_type = Column(String(50))
    is_valid = Column(Boolean)
    is_active = Column(Boolean)

    # Owner information
    owner_name = Column(String(200))
    owner_address = Column(String(500))

    # Location
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    timezone = Column(String(50))

    # Metadata
    last_verified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_phone_owner", "owner_name"),)


class EmailRecord(Base):
    """Email address records."""

    __tablename__ = "email_records"

    email = Column(String(200), primary_key=True)
    is_valid = Column(Boolean)
    is_deliverable = Column(Boolean)
    is_disposable = Column(Boolean)
    is_free_provider = Column(Boolean)
    is_role_based = Column(Boolean)

    # Domain info
    domain = Column(String(100))
    mx_records = Column(JSON)

    # Social profiles
    social_profiles = Column(JSON)

    # Metadata
    last_verified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_email_domain", "domain"),)


class BatchJob(Base):
    """Batch processing job records."""

    __tablename__ = "batch_jobs"

    id = Column(String(50), primary_key=True)
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    total_items = Column(Integer, nullable=False)
    processed_items = Column(Integer, default=0)
    successful_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)

    # Job data
    input_data = Column(JSON)
    results = Column(JSON)
    errors = Column(JSON)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_time = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))

    __table_args__ = (
        Index("idx_batch_status", "status"),
        Index("idx_batch_created", "created_at"),
    )


class DatabaseIntegration:
    """Database integration for sleuth-intel."""

    def __init__(self, database_url: str):
        # Convert to async URL if needed
        if database_url.startswith("postgresql://"):
            async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            async_url = database_url

        self.engine = create_async_engine(async_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession)
        self.client = SleuthIntel()

    async def initialize_database(self):
        """Create database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database initialized")

    async def search_and_store_person(
        self, search_params: Dict[str, Any], update_existing: bool = True
    ) -> str:
        """
        Search for a person and store results in database.

        Args:
            search_params: Person search parameters
            update_existing: Whether to update existing records

        Returns:
            Search record ID
        """
        search_id = hashlib.sha256(
            f"{search_params}{datetime.now()}".encode()
        ).hexdigest()[:12]

        start_time = datetime.now()

        # Create search record
        async with self.async_session() as session:
            search_record = SearchRecord(
                id=search_id,
                search_type="person",
                search_params=search_params,
                status="processing",
            )
            session.add(search_record)
            await session.commit()

        try:
            # Perform search
            request = PersonSearchRequest(**search_params)
            response = await self.client.person_search(request)

            if response.success and response.results:
                # Store person records
                async with self.async_session() as session:
                    for result in response.results[:10]:  # Limit to top 10
                        person_id = hashlib.sha256(
                            f"{result.get('first_name')}{result.get('last_name')}{result.get('date_of_birth', '')}".encode()
                        ).hexdigest()[:12]

                        # Check if person exists
                        existing = await session.get(PersonRecord, person_id)

                        if existing and not update_existing:
                            continue

                        if existing:
                            # Update existing record
                            existing.phones = result.get("phones", [])
                            existing.emails = result.get("emails", [])
                            existing.addresses = result.get("addresses", [])
                            existing.relatives = result.get("relatives", [])
                            existing.associates = result.get("associates", [])
                            existing.confidence_score = result.get(
                                "match_confidence", 0
                            )
                            existing.last_verified = datetime.now()
                        else:
                            # Create new record
                            person = PersonRecord(
                                id=person_id,
                                first_name=result.get("first_name"),
                                last_name=result.get("last_name"),
                                middle_name=result.get("middle_name"),
                                date_of_birth=result.get("date_of_birth"),
                                age=result.get("age"),
                                ssn_last4=result.get("ssn_last4"),
                                phones=result.get("phones", []),
                                emails=result.get("emails", []),
                                addresses=result.get("addresses", []),
                                relatives=result.get("relatives", []),
                                associates=result.get("associates", []),
                                confidence_score=result.get("match_confidence", 0),
                                last_verified=datetime.now(),
                            )
                            session.add(person)

                    # Update search record
                    search_record = await session.get(SearchRecord, search_id)
                    search_record.status = "completed"
                    search_record.result_count = len(response.results)
                    search_record.results = response.results[:10]
                    search_record.processing_time = (
                        datetime.now() - start_time
                    ).total_seconds()

                    await session.commit()

                print(f"✅ Stored {len(response.results)} person records")
            else:
                # No results found
                async with self.async_session() as session:
                    search_record = await session.get(SearchRecord, search_id)
                    search_record.status = "no_results"
                    search_record.processing_time = (
                        datetime.now() - start_time
                    ).total_seconds()
                    await session.commit()

                print("⚠️ No results found")

        except Exception as e:
            # Handle error
            async with self.async_session() as session:
                search_record = await session.get(SearchRecord, search_id)
                search_record.status = "failed"
                search_record.error_message = str(e)
                search_record.processing_time = (
                    datetime.now() - start_time
                ).total_seconds()
                await session.commit()

            print(f"❌ Search failed: {str(e)}")
            raise

        return search_id

    async def verify_and_store_phones(self, phone_numbers: List[str]) -> Dict[str, Any]:
        """
        Verify phone numbers and store in database.

        Args:
            phone_numbers: List of phone numbers

        Returns:
            Verification summary
        """
        summary = {
            "total": len(phone_numbers),
            "verified": 0,
            "invalid": 0,
            "errors": 0,
        }

        for phone in phone_numbers:
            try:
                # Check if already in database
                async with self.async_session() as session:
                    existing = await session.get(PhoneRecord, phone)

                    # Skip if recently verified
                    if existing and existing.last_verified:
                        age = datetime.now() - existing.last_verified
                        if age.days < 30:  # Skip if verified within 30 days
                            print(f"⏩ Skipping {phone} (recently verified)")
                            summary["verified"] += 1
                            continue

                # Verify phone
                request = PhoneLookupRequest(phone=phone)
                response = await self.client.phone_lookup(request)

                if response.success:
                    async with self.async_session() as session:
                        if existing:
                            # Update existing record
                            existing.phone_type = response.phone_type
                            existing.carrier = response.carrier
                            existing.line_type = response.line_type
                            existing.is_valid = response.is_valid
                            existing.is_active = response.is_current
                            existing.last_verified = datetime.now()

                            if response.owner_info:
                                existing.owner_name = response.owner_info.get("name")
                                existing.owner_address = response.owner_info.get(
                                    "address"
                                )

                            if response.location_info:
                                existing.city = response.location_info.get("city")
                                existing.state = response.location_info.get("state")
                                existing.zip_code = response.location_info.get(
                                    "zip_code"
                                )
                                existing.timezone = response.location_info.get(
                                    "timezone"
                                )
                        else:
                            # Create new record
                            phone_record = PhoneRecord(
                                phone_number=phone,
                                phone_type=response.phone_type,
                                carrier=response.carrier,
                                line_type=response.line_type,
                                is_valid=response.is_valid,
                                is_active=response.is_current,
                                last_verified=datetime.now(),
                            )

                            if response.owner_info:
                                phone_record.owner_name = response.owner_info.get(
                                    "name"
                                )
                                phone_record.owner_address = response.owner_info.get(
                                    "address"
                                )

                            if response.location_info:
                                phone_record.city = response.location_info.get("city")
                                phone_record.state = response.location_info.get("state")
                                phone_record.zip_code = response.location_info.get(
                                    "zip_code"
                                )
                                phone_record.timezone = response.location_info.get(
                                    "timezone"
                                )

                            session.add(phone_record)

                        await session.commit()

                    if response.is_valid:
                        summary["verified"] += 1
                        print(f"✅ {phone} - Valid")
                    else:
                        summary["invalid"] += 1
                        print(f"❌ {phone} - Invalid")
                else:
                    summary["errors"] += 1
                    print(f"⚠️ {phone} - Verification failed")

            except Exception as e:
                summary["errors"] += 1
                print(f"❌ {phone} - Error: {str(e)}")

            # Rate limiting
            await asyncio.sleep(0.5)

        return summary

    async def verify_and_store_emails(
        self, email_addresses: List[str]
    ) -> Dict[str, Any]:
        """
        Verify email addresses and store in database.

        Args:
            email_addresses: List of email addresses

        Returns:
            Verification summary
        """
        summary = {
            "total": len(email_addresses),
            "valid": 0,
            "invalid": 0,
            "disposable": 0,
            "errors": 0,
        }

        for email in email_addresses:
            try:
                # Check if already in database
                async with self.async_session() as session:
                    existing = await session.get(EmailRecord, email)

                    # Skip if recently verified
                    if existing and existing.last_verified:
                        age = datetime.now() - existing.last_verified
                        if age.days < 7:  # Skip if verified within 7 days
                            print(f"⏩ Skipping {email} (recently verified)")
                            if existing.is_valid:
                                summary["valid"] += 1
                            else:
                                summary["invalid"] += 1
                            continue

                # Verify email
                request = EmailVerificationRequest(email=email)
                response = await self.client.email_verification(request)

                if response.success:
                    async with self.async_session() as session:
                        if existing:
                            # Update existing record
                            existing.is_valid = response.is_valid
                            existing.is_deliverable = response.is_deliverable
                            existing.is_disposable = response.is_disposable
                            existing.is_free_provider = response.is_free_provider
                            existing.is_role_based = response.is_role_based
                            existing.domain = response.domain
                            existing.mx_records = response.mx_records
                            existing.social_profiles = response.social_profiles
                            existing.last_verified = datetime.now()
                        else:
                            # Create new record
                            email_record = EmailRecord(
                                email=email,
                                is_valid=response.is_valid,
                                is_deliverable=response.is_deliverable,
                                is_disposable=response.is_disposable,
                                is_free_provider=response.is_free_provider,
                                is_role_based=response.is_role_based,
                                domain=response.domain,
                                mx_records=response.mx_records,
                                social_profiles=response.social_profiles,
                                last_verified=datetime.now(),
                            )
                            session.add(email_record)

                        await session.commit()

                    if response.is_valid:
                        summary["valid"] += 1
                        if response.is_disposable:
                            summary["disposable"] += 1
                        print(f"✅ {email} - Valid")
                    else:
                        summary["invalid"] += 1
                        print(f"❌ {email} - Invalid")
                else:
                    summary["errors"] += 1
                    print(f"⚠️ {email} - Verification failed")

            except Exception as e:
                summary["errors"] += 1
                print(f"❌ {email} - Error: {str(e)}")

            # Rate limiting
            await asyncio.sleep(0.3)

        return summary

    async def run_batch_job(
        self, job_type: str, items: List[Any], created_by: str = "system"
    ) -> str:
        """
        Run a batch processing job.

        Args:
            job_type: Type of batch job
            items: Items to process
            created_by: User/system creating the job

        Returns:
            Batch job ID
        """
        batch_id = hashlib.sha256(
            f"{job_type}{len(items)}{datetime.now()}".encode()
        ).hexdigest()[:12]

        # Create batch job record
        async with self.async_session() as session:
            batch_job = BatchJob(
                id=batch_id,
                job_type=job_type,
                status="pending",
                total_items=len(items),
                input_data=items,
                created_by=created_by,
                started_at=datetime.now(),
            )
            session.add(batch_job)
            await session.commit()

        print(f"\n📦 Starting batch job: {batch_id}")
        print(f"Type: {job_type}")
        print(f"Items: {len(items)}")

        try:
            # Update status to processing
            async with self.async_session() as session:
                batch_job = await session.get(BatchJob, batch_id)
                batch_job.status = "processing"
                await session.commit()

            results = []
            errors = []

            # Process items based on job type
            if job_type == "person_search":
                for item in items:
                    try:
                        search_id = await self.search_and_store_person(item)
                        results.append({"input": item, "search_id": search_id})

                        # Update progress
                        async with self.async_session() as session:
                            batch_job = await session.get(BatchJob, batch_id)
                            batch_job.processed_items += 1
                            batch_job.successful_items += 1
                            await session.commit()

                    except Exception as e:
                        errors.append({"input": item, "error": str(e)})

                        async with self.async_session() as session:
                            batch_job = await session.get(BatchJob, batch_id)
                            batch_job.processed_items += 1
                            batch_job.failed_items += 1
                            await session.commit()

                    await asyncio.sleep(1)  # Rate limiting

            elif job_type == "phone_verification":
                phone_numbers = [
                    item.get("phone") for item in items if item.get("phone")
                ]
                summary = await self.verify_and_store_phones(phone_numbers)
                results.append(summary)

                async with self.async_session() as session:
                    batch_job = await session.get(BatchJob, batch_id)
                    batch_job.processed_items = summary["total"]
                    batch_job.successful_items = summary["verified"]
                    batch_job.failed_items = summary["invalid"] + summary["errors"]
                    await session.commit()

            elif job_type == "email_verification":
                email_addresses = [
                    item.get("email") for item in items if item.get("email")
                ]
                summary = await self.verify_and_store_emails(email_addresses)
                results.append(summary)

                async with self.async_session() as session:
                    batch_job = await session.get(BatchJob, batch_id)
                    batch_job.processed_items = summary["total"]
                    batch_job.successful_items = summary["valid"]
                    batch_job.failed_items = summary["invalid"] + summary["errors"]
                    await session.commit()

            # Update batch job as completed
            async with self.async_session() as session:
                batch_job = await session.get(BatchJob, batch_id)
                batch_job.status = "completed"
                batch_job.results = results
                batch_job.errors = errors
                batch_job.completed_at = datetime.now()
                batch_job.processing_time = (
                    batch_job.completed_at - batch_job.started_at
                ).total_seconds()
                await session.commit()

            print(f"✅ Batch job completed: {batch_id}")
            print(
                f"   Successful: {batch_job.successful_items}/{batch_job.total_items}"
            )

        except Exception as e:
            # Mark job as failed
            async with self.async_session() as session:
                batch_job = await session.get(BatchJob, batch_id)
                batch_job.status = "failed"
                batch_job.errors = [{"error": str(e)}]
                batch_job.completed_at = datetime.now()
                await session.commit()

            print(f"❌ Batch job failed: {str(e)}")
            raise

        return batch_id

    async def query_person_records(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 10,
    ) -> List[PersonRecord]:
        """
        Query person records from database.

        Args:
            first_name: Filter by first name
            last_name: Filter by last name
            min_confidence: Minimum confidence score
            limit: Maximum records to return

        Returns:
            List of person records
        """
        async with self.async_session() as session:
            query = select(PersonRecord)

            # Apply filters
            conditions = []
            if first_name:
                conditions.append(PersonRecord.first_name.ilike(f"%{first_name}%"))
            if last_name:
                conditions.append(PersonRecord.last_name.ilike(f"%{last_name}%"))
            if min_confidence:
                conditions.append(PersonRecord.confidence_score >= min_confidence)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        async with self.async_session() as session:
            # Count records
            person_count = await session.execute(select(PersonRecord).count())
            phone_count = await session.execute(select(PhoneRecord).count())
            email_count = await session.execute(select(EmailRecord).count())
            search_count = await session.execute(select(SearchRecord).count())
            batch_count = await session.execute(select(BatchJob).count())

            # Get recent activity
            recent_searches = await session.execute(
                select(SearchRecord)
                .where(SearchRecord.created_at >= datetime.now() - timedelta(days=1))
                .count()
            )

            return {
                "total_records": {
                    "persons": person_count,
                    "phones": phone_count,
                    "emails": email_count,
                    "searches": search_count,
                    "batch_jobs": batch_count,
                },
                "recent_activity": {"searches_last_24h": recent_searches},
            }

    async def close(self):
        """Clean up resources."""
        await self.client.close()
        await self.engine.dispose()


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Database Integration Example")
    print("=" * 60)

    # Use SQLite for demo (replace with your database URL)
    database_url = "sqlite+aiosqlite:///sleuth_intel.db"

    integration = DatabaseIntegration(database_url)

    # Initialize database
    await integration.initialize_database()

    # Example 1: Search and store person
    print("\n📌 Example 1: Person Search and Storage")
    print("-" * 40)

    search_params = {
        "first_name": "John",
        "last_name": "Smith",
        "city": "Los Angeles",
        "state": "CA",
    }

    try:
        search_id = await integration.search_and_store_person(search_params)
        print(f"✅ Search completed: {search_id}")

    except Exception as e:
        print(f"❌ Search failed: {str(e)}")

    # Example 2: Batch phone verification
    print("\n📌 Example 2: Batch Phone Verification")
    print("-" * 40)

    phone_numbers = ["5551234567", "5559876543", "5555551212"]

    try:
        summary = await integration.verify_and_store_phones(phone_numbers)
        print(f"✅ Phone verification completed:")
        print(f"   Valid: {summary['verified']}/{summary['total']}")
        print(f"   Invalid: {summary['invalid']}")

    except Exception as e:
        print(f"❌ Phone verification failed: {str(e)}")

    # Example 3: Batch email verification
    print("\n📌 Example 3: Batch Email Verification")
    print("-" * 40)

    email_addresses = ["test@example.com", "info@company.com", "user@gmail.com"]

    try:
        summary = await integration.verify_and_store_emails(email_addresses)
        print(f"✅ Email verification completed:")
        print(f"   Valid: {summary['valid']}/{summary['total']}")
        print(f"   Disposable: {summary['disposable']}")

    except Exception as e:
        print(f"❌ Email verification failed: {str(e)}")

    # Example 4: Run batch job
    print("\n📌 Example 4: Batch Job Processing")
    print("-" * 40)

    batch_items = [
        {"first_name": "Jane", "last_name": "Doe", "state": "NY"},
        {"first_name": "Bob", "last_name": "Johnson", "state": "TX"},
        {"first_name": "Alice", "last_name": "Williams", "state": "FL"},
    ]

    try:
        batch_id = await integration.run_batch_job(
            job_type="person_search", items=batch_items, created_by="demo_user"
        )
        print(f"✅ Batch job completed: {batch_id}")

    except Exception as e:
        print(f"❌ Batch job failed: {str(e)}")

    # Example 5: Query database
    print("\n📌 Example 5: Database Query")
    print("-" * 40)

    records = await integration.query_person_records(
        first_name="John", min_confidence=70, limit=5
    )

    print(f"Found {len(records)} person records:")
    for record in records:
        print(
            f"  • {record.first_name} {record.last_name} (Confidence: {record.confidence_score}%)"
        )

    # Get statistics
    stats = await integration.get_statistics()
    print("\n📊 Database Statistics:")
    print(f"   Persons: {stats['total_records']['persons']}")
    print(f"   Phones: {stats['total_records']['phones']}")
    print(f"   Emails: {stats['total_records']['emails']}")
    print(f"   Searches: {stats['total_records']['searches']}")

    # Clean up
    await integration.close()

    print("\n✨ Database integration example completed!")


if __name__ == "__main__":
    asyncio.run(main())
