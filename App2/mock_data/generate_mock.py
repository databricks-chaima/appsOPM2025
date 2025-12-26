"""
Mock Data Generator for CCD Welding Quality Control App

Generates realistic inspection records matching the Unity Catalog schema.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Factory configuration: 40 factories with 2 cameras each
FACTORIES = [
    "WUH-G426", "WUH-A79", "WUH-L42P", "WUH-BX11", "WUH-KX11",
    "YAN-YT01", "YAN-YT02", "YAN-YT03", "YAN-YT04", "YAN-YT05",
    "NGB-NB10", "NGB-NB11", "NGB-NB12", "NGB-NB13", "NGB-NB14",
    "GUA-GZ01", "GUA-GZ02", "GUA-GZ03", "GUA-GZ04", "GUA-GZ05",
    "SHE-SY01", "SHE-SY02", "SHE-SY03", "SHE-SY04", "SHE-SY05",
    "KYO-KY01", "KYO-KY02", "KYO-KY03", "KYO-KY04", "KYO-KY05",
    "RAY-RY01", "RAY-RY02", "RAY-RY03", "RAY-RY04", "RAY-RY05",
    "SHA-SH01", "SHA-SH02", "SHA-SH03", "SHA-SH04", "SHA-SH05",
]

CAMERAS = ["CAM-01", "CAM-02"]

# Defect types for KO predictions
DEFECT_TYPES = [
    "weld_crack",
    "porosity",
    "undercut",
    "spatter",
    "incomplete_fusion",
    "burn_through",
    "misalignment",
]

# Model versions
MODEL_VERSIONS = ["v2.3.1", "v2.3.0", "v2.2.5"]

# Image volume path and available photos
IMAGE_VOLUME_PATH = "/Volumes/serverless_opm_catalog/opm/quality/images-highres"
NUM_PHOTOS = 10  # photo1.jpg to photo10.jpg


def generate_inspection_id(index: int) -> str:
    """Generate a unique inspection ID"""
    return f"INSP-2025-{index:06d}"


def get_image_path(index: int) -> str:
    """Generate image path cycling through available photos (1-10)"""
    photo_num = (index % NUM_PHOTOS) + 1  # Cycles 1, 2, 3, ... 10, 1, 2, ...
    return f"{IMAGE_VOLUME_PATH}/photo{photo_num}.jpg"


def generate_factories_json() -> list:
    """Generate simple factory list"""
    factories = []
    for factory_id in FACTORIES:
        region = factory_id.split("-")[0]
        factories.append({
            "factory_id": factory_id,
            "region": region,
            "cameras": CAMERAS.copy()
        })
    return factories


def generate_inspections_json(num_records: int = 500) -> list:
    """Generate inspection records with exact schema"""
    inspections = []
    
    # Generate records over the past 7 days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    for i in range(num_records):
        # Random timestamp within the date range
        random_seconds = random.randint(0, int((end_time - start_time).total_seconds()))
        timestamp = start_time + timedelta(seconds=random_seconds)
        
        # Random factory and camera
        factory_id = random.choice(FACTORIES)
        camera_id = random.choice(CAMERAS)
        
        # Prediction: 95% OK, 5% KO
        is_ok = random.random() < 0.95
        prediction = "OK" if is_ok else "KO"
        
        # Confidence score
        if is_ok:
            confidence_score = round(random.uniform(0.92, 0.99), 4)
        else:
            confidence_score = round(random.uniform(0.75, 0.95), 4)
        
        # Defect type (null if OK)
        defect_type = None if is_ok else random.choice(DEFECT_TYPES)
        
        # Generate inspection record matching exact schema
        inspection = {
            "inspection_id": generate_inspection_id(i + 1),
            "factory_id": factory_id,
            "camera_id": camera_id,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "image_path": get_image_path(i),
            "prediction": prediction,
            "confidence_score": confidence_score,
            "defect_type": defect_type,
            "inference_time_ms": random.randint(45, 180),
            "model_version": random.choice(MODEL_VERSIONS),
            "date": timestamp.strftime("%Y-%m-%d")
        }
        
        inspections.append(inspection)
    
    # Sort by timestamp descending (most recent first)
    inspections.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return inspections


def main():
    """Generate all mock data files"""
    output_dir = Path(__file__).parent
    
    # Generate factories
    print("Generating factories.json...")
    factories = generate_factories_json()
    with open(output_dir / "factories.json", "w") as f:
        json.dump(factories, f, indent=2)
    print(f"  Created factories.json with {len(factories)} factories")
    
    # Generate inspections
    print("Generating inspections.json...")
    inspections = generate_inspections_json(500)
    with open(output_dir / "inspections.json", "w") as f:
        json.dump(inspections, f, indent=2)
    print(f"  Created inspections.json with {len(inspections)} records")
    
    # Print sample record
    print("\nSample inspection record:")
    print(json.dumps(inspections[0], indent=2))
    
    print("\nMock data generation complete!")


if __name__ == "__main__":
    main()
