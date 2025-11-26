#!/usr/bin/env python3
"""
Remove dummy/test data from the database.
This script identifies and removes test data while preserving real synced data.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / ".env")

from backend.api.database import SessionLocal
from backend.api.models import Item, ActionProposal, ItemAgentMetadata


def remove_dummy_data():
    """Remove dummy/test data from database."""
    db = SessionLocal()

    try:
        # Get all items
        items = db.query(Item).all()
        print(f"Found {len(items)} items in database")

        # Identify dummy data - typically has test patterns
        dummy_patterns = [
            "Newsletter:",
            "Invoice from vendor",
            "Team standup",
            "URGENT: Project deadline",
            "techdigest.com",
            "vendor.com",
            "billing@vendor.com",
            "newsletter@techdigest.com",
            "boss@company.com",
        ]

        items_to_delete = []
        for item in items:
            # Check if item matches dummy patterns
            is_dummy = False
            if item.title:
                for pattern in dummy_patterns:
                    if pattern.lower() in item.title.lower():
                        is_dummy = True
                        break

            if item.sender:
                for pattern in dummy_patterns:
                    if pattern.lower() in item.sender.lower():
                        is_dummy = True
                        break

            # Also check if it's from a test/dummy source
            if item.source_provider not in ["gmail", "outlook", "google_calendar"]:
                is_dummy = True

            if is_dummy:
                items_to_delete.append(item)

        print(f"\nIdentified {len(items_to_delete)} dummy items to remove:")
        for item in items_to_delete[:10]:
            print(f"  - {item.title} ({item.source_provider})")
        if len(items_to_delete) > 10:
            print(f"  ... and {len(items_to_delete) - 10} more")

        # Get all action proposals
        actions = db.query(ActionProposal).all()
        print(f"\nFound {len(actions)} action proposals")

        # Identify dummy actions - check if they're related to dummy items
        dummy_item_ids = {item.id for item in items_to_delete}
        actions_to_delete = []

        for action in actions:
            # If action is related to a dummy item, delete it
            if action.related_item_id and action.related_item_id in dummy_item_ids:
                actions_to_delete.append(action)
            # Also check for dummy patterns in explanation
            elif action.explanation:
                for pattern in dummy_patterns:
                    if pattern.lower() in action.explanation.lower():
                        actions_to_delete.append(action)
                        break

        print(f"Identified {len(actions_to_delete)} dummy actions to remove:")
        for action in actions_to_delete[:5]:
            print(f"  - {action.action_type}: {action.explanation[:50]}...")
        if len(actions_to_delete) > 5:
            print(f"  ... and {len(actions_to_delete) - 5} more")

        # Confirm deletion
        if items_to_delete or actions_to_delete:
            response = input(
                f"\n[WARNING]  Delete {len(items_to_delete)} items and {len(actions_to_delete)} actions? (yes/no): "
            )
            if response.lower() == "yes":
                # Delete actions first (they reference items)
                for action in actions_to_delete:
                    db.delete(action)

                # Delete item metadata
                for item in items_to_delete:
                    metadata = db.query(ItemAgentMetadata).filter(ItemAgentMetadata.item_id == item.id).first()
                    if metadata:
                        db.delete(metadata)

                # Delete items
                for item in items_to_delete:
                    db.delete(item)

                db.commit()
                print(f"\n[OK] Deleted {len(items_to_delete)} items and {len(actions_to_delete)} actions")

                # Show remaining counts
                remaining_items = db.query(Item).count()
                remaining_actions = db.query(ActionProposal).count()
                print(f"\nRemaining: {remaining_items} items, {remaining_actions} actions")
            else:
                print("\n[ERROR] Deletion cancelled")
        else:
            print("\n[OK] No dummy data found - database is clean!")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  Remove Dummy/Test Data")
    print("=" * 60)
    print()
    remove_dummy_data()
