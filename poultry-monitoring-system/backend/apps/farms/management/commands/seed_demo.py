"""Seed clearly-labelled demonstration data.

All demo records are tagged (``is_demo=True`` where available, demo usernames,
farm code DEMO-*) so they can be told apart from real GreenFarms data. Run with
``--reset`` to remove previously-seeded demo data first.

This generates plausible but synthetic operational records. It does NOT
fabricate ML model metrics, sensor calibration, or experimental results.
"""
import random
import uuid
from datetime import timedelta

from apps.accounts.constants import (
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_OWNER,
    ROLE_VET,
    ROLE_WORKER,
)
from apps.accounts.models import CustomUser
from apps.alerts.models import Alert
from apps.farms.models import Breed, Customer, Farm, Pen, Supplier
from apps.feeding.models import FeedType, FeedUsage
from apps.finance.models import Expense, Payment, Sale
from apps.flocks.models import (
    Batch,
    ChickEntry,
    DailyObservation,
    MortalityRecord,
    WeightRecord,
)
from apps.health.models import (
    HealthObservation,
    Medication,
    TreatmentRecord,
    VaccinationRecord,
    VaccinationSchedule,
)
from apps.inventory.models import InventoryCategory, InventoryItem, StockMovement
from apps.iot.models import (
    DeviceConfiguration,
    DeviceToken,
    EnvironmentalThreshold,
    IoTDevice,
    SensorReading,
)
from apps.vision.models import VisionResult
from apps.vision.services import process_vision_result
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

DEMO_PASSWORD = "DemoPass123!"
DEMO_FARM_CODE = "DEMO-YDE-01"


class Command(BaseCommand):
    help = "Create demonstration data (clearly labelled as demo)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data first")

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(42)
        call_command("setup_roles")

        if options["reset"]:
            Farm.objects.filter(is_demo=True).delete()
            CustomUser.objects.filter(username__startswith="demo_").delete()
            self.stdout.write("Removed previous demo data.")

        users = self._users()
        owner = users[ROLE_OWNER]

        farm, _ = Farm.objects.update_or_create(
            code=DEMO_FARM_CODE,
            defaults={
                "name": "GreenFarms Demo Yaoundé",
                "city": "Yaoundé",
                "region": "Centre",
                "owner": owner,
                "is_demo": True,
            },
        )
        for u in users.values():
            if u.role in (ROLE_MANAGER, ROLE_WORKER, ROLE_VET):
                u.assigned_farms.add(farm)

        pens = [
            Pen.objects.get_or_create(
                farm=farm, code=f"P{i}",
                defaults={"name": f"House {i}", "capacity": 1000},
            )[0]
            for i in range(1, 4)
        ]
        breed, _ = Breed.objects.get_or_create(name="Cobb 500")
        supplier, _ = Supplier.objects.get_or_create(name="Demo Hatchery Ltd", defaults={"supplies": "chicks"})
        customer, _ = Customer.objects.get_or_create(name="Demo Market Buyer", defaults={"customer_type": "retailer"})

        # Inventory
        cat, _ = InventoryCategory.objects.get_or_create(name="Feed")
        feed_item, _ = InventoryItem.objects.get_or_create(
            farm=farm, name="Starter feed (demo)",
            defaults={"category": cat, "unit": "kg", "opening_stock": 2000, "reorder_level": 300, "unit_cost": 350},
        )
        StockMovement.objects.get_or_create(
            item=feed_item, movement_type=StockMovement.Type.RECEIPT, quantity=1000,
            reference="DEMO-RECEIPT",
        )
        feed_type, _ = FeedType.objects.get_or_create(
            name="Starter (demo)", defaults={"phase": FeedType.Phase.STARTER, "inventory_item": feed_item}
        )

        # Batch
        start = timezone.localdate() - timedelta(days=28)
        batch, _ = Batch.objects.update_or_create(
            farm=farm, code="DEMO-B1",
            defaults={"pen": pens[0], "breed": breed, "start_date": start,
                      "status": Batch.Status.ACTIVE, "is_demo": True},
        )
        ChickEntry.objects.get_or_create(
            batch=batch, source_reference="DEMO",
            defaults={"supplier": supplier, "entry_date": start, "quantity": 1000, "unit_cost": 500},
        )

        # Daily mortality, feed, weights, observations across the batch age.
        for day in range(0, 28, 2):
            d = start + timedelta(days=day)
            MortalityRecord.objects.get_or_create(
                batch=batch, record_date=d, cause=MortalityRecord.Cause.UNKNOWN,
                defaults={"pen": pens[0], "quantity": rng.randint(0, 4)},
            )
            FeedUsage.objects.get_or_create(
                batch=batch, feed_type=feed_type, record_date=d,
                defaults={"pen": pens[0], "quantity_kg": rng.randint(40, 90)},
            )
            if day % 7 == 0:
                WeightRecord.objects.get_or_create(
                    batch=batch, record_date=d,
                    defaults={"sample_size": 20, "average_weight_g": 120 + day * 65},
                )
            DailyObservation.objects.get_or_create(
                batch=batch, record_date=d,
                defaults={"pen": pens[0], "behaviour": "normal", "water_consumption_l": rng.randint(80, 160)},
            )

        # Health + vaccination
        med, _ = Medication.objects.get_or_create(name="Newcastle vaccine (demo)", defaults={"medication_type": "vaccine"})
        sched, _ = VaccinationSchedule.objects.get_or_create(
            batch=batch, medication=med, vaccine_name="Newcastle (demo)",
            defaults={"scheduled_age_days": 7},
        )
        VaccinationRecord.objects.get_or_create(
            batch=batch, medication=med, vaccine_name="Newcastle (demo)",
            defaults={"schedule": sched, "administered_date": start + timedelta(days=7), "quantity": 990},
        )
        obs, _ = HealthObservation.objects.get_or_create(
            batch=batch, title="Mild lethargy observed (demo)",
            defaults={"pen": pens[0], "severity": HealthObservation.Severity.MILD,
                      "symptoms": "A few birds less active in the morning.", "affected_count": 5},
        )
        TreatmentRecord.objects.get_or_create(
            batch=batch, medication=med, treatment_date=timezone.localdate(),
            defaults={"dosage": "as labelled", "quantity_used": 1},
        )

        # Finance
        Expense.objects.get_or_create(
            farm=farm, description="Day-old chicks (demo)",
            defaults={"batch": batch, "category": Expense.Category.CHICKS, "amount": 500000},
        )
        sale, _ = Sale.objects.get_or_create(
            farm=farm, batch=batch, reference="DEMO-SALE-1",
            defaults={"customer": customer, "quantity": 50, "unit_price": 3500,
                      "status": Sale.Status.CONFIRMED},
        )
        Payment.objects.get_or_create(sale=sale, reference="DEMO-PAY-1", defaults={"amount": 100000})

        # IoT device + readings + thresholds
        device, _ = IoTDevice.objects.get_or_create(
            device_id="DEMO-PI-001",
            defaults={"name": "Demo Raspberry Pi", "farm": farm, "pen": pens[0], "is_demo": True},
        )
        DeviceConfiguration.objects.get_or_create(device=device)
        EnvironmentalThreshold.objects.get_or_create(
            farm=farm, pen=pens[0],
            defaults={"temp_max_c": 32, "temp_min_c": 20, "humidity_max_pct": 75},
        )
        if not device.tokens.exists():
            _, raw = DeviceToken.issue(device, label="demo")
            self.stdout.write(self.style.WARNING(f"Demo device token (store securely, shown once): {raw}"))

        now = timezone.now()
        for h in range(48):
            ts = now - timedelta(hours=h)
            SensorReading.objects.get_or_create(
                reading_uuid=uuid.uuid4(),
                defaults={
                    "device": device, "farm": farm, "pen": pens[0], "batch": batch,
                    "temperature_c": round(26 + rng.uniform(-3, 6), 1),
                    "humidity_pct": round(60 + rng.uniform(-10, 12), 1),
                    "raw_gas_value": rng.uniform(100, 400),
                    "gas_risk_value": round(rng.uniform(0.1, 0.7), 2),
                    "server_timestamp": ts, "device_timestamp": ts,
                    "fan_state": rng.random() > 0.5,
                },
            )

        # Vision results (synthetic, clearly demo) — exercises the alert path.
        for cls, conf in [("healthy", 0.91), ("lethargic", 0.62), ("open_beak_stress", 0.58)]:
            vr, created = VisionResult.objects.get_or_create(
                result_uuid=uuid.uuid4(),
                defaults={
                    "device": device, "farm": farm, "pen": pens[0], "batch": batch,
                    "predicted_class": cls, "confidence": conf, "detection_count": 1,
                    "detections": [{"cls": cls, "confidence": conf, "bbox": [10, 10, 80, 80]}],
                    "model_name": "yolo11n", "model_version": "demo",
                    "image_reference": "demo://sample-frame.jpg",
                },
            )
            if created:
                process_vision_result(vr)

        n_alerts = Alert.objects.filter(farm=farm).count()
        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready. Farm '{farm.name}', batch {batch.code}, "
            f"current flock {batch.current_quantity}, {n_alerts} alerts. "
            f"Login users: demo_admin / demo_owner / demo_manager / demo_worker / demo_vet "
            f"(password: {DEMO_PASSWORD})."
        ))

    def _users(self):
        spec = {
            ROLE_ADMIN: ("demo_admin", True, True),
            ROLE_OWNER: ("demo_owner", False, False),
            ROLE_MANAGER: ("demo_manager", False, False),
            ROLE_WORKER: ("demo_worker", False, False),
            ROLE_VET: ("demo_vet", False, False),
        }
        users = {}
        for role, (username, staff, superuser) in spec.items():
            user, created = CustomUser.objects.get_or_create(
                username=username,
                defaults={"role": role, "is_staff": staff, "is_superuser": superuser,
                          "first_name": role.title(), "last_name": "Demo"},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.role = role
                user.is_staff = staff
                user.is_superuser = superuser
                user.save()
            user.sync_primary_group()
            users[role] = user
        return users
