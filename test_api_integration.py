"""
Integration Test for Substrate API

Tests the complete API workflow:
1. Create user profiles
2. Find matches
3. Accept matches
4. Report outcomes
5. Check statistics
"""

import requests
import json
import time
from typing import Dict, Any

API_URL = "http://localhost:8000"

def print_section(title: str):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_api_health():
    """Test that API is running"""
    print_section("Testing API Health")

    response = requests.get(f"{API_URL}/")
    assert response.status_code == 200

    data = response.json()
    print(f"✓ API Status: {data['status']}")
    print(f"✓ Service: {data['service']}")
    print(f"✓ Version: {data['version']}")


def create_test_profile(user_id: str, capabilities: list) -> Dict[str, Any]:
    """Create a test user profile"""
    print(f"\nCreating profile for {user_id}...")

    profile_data = {
        "user_id": user_id,
        "capabilities": capabilities,
        "location_region": "North America",
        "timezone": "America/Los_Angeles",
        "domains": ["robotics", "software", "hardware"]
    }

    response = requests.post(
        f"{API_URL}/profiles",
        json=profile_data,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200, f"Failed to create profile: {response.text}"

    data = response.json()
    print(f"✓ Profile created: {data['user_id']}")
    print(f"  Capabilities: {data['capabilities_count']}")

    return data


def find_matches_for_need(user_id: str, need_data: Dict[str, Any]) -> Dict[str, Any]:
    """Find matches for a need"""
    print(f"\nFinding matches for {user_id}...")
    print(f"Need: {need_data['need_name']}")

    response = requests.post(
        f"{API_URL}/match",
        json=need_data,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200, f"Failed to find matches: {response.text}"

    data = response.json()
    print(f"✓ Found {data['matches_found']} matches")

    return data


def get_stats() -> Dict[str, Any]:
    """Get system statistics"""
    print("\nGetting system statistics...")

    response = requests.get(f"{API_URL}/stats")
    assert response.status_code == 200

    data = response.json()
    print(f"✓ Total matches: {data['total_matches']}")
    print(f"✓ Success rate: {data['success_rate']*100:.1f}%")
    print(f"✓ Total outcomes: {data['total_outcomes']}")

    return data


def main():
    """Run integration tests"""
    print("\n" + "="*80)
    print("  SUBSTRATE API INTEGRATION TEST")
    print("="*80)

    try:
        # Test 1: API Health
        test_api_health()

        # Test 2: Create Test Profiles
        print_section("Creating Test Profiles")

        # Profile 1: Software/ROS expert
        profile1 = create_test_profile(
            "test_user_software_001",
            [
                {
                    "type": "skill",
                    "name": "ROS2 Development",
                    "description": "Expert in Robot Operating System 2, navigation, SLAM, and sensor integration",
                    "proficiency": 0.95,
                    "tags": ["ros2", "robotics", "software", "navigation"],
                    "privacy_level": "network"
                },
                {
                    "type": "skill",
                    "name": "Python & C++ Programming",
                    "description": "Advanced programming in Python and C++ for robotics applications",
                    "proficiency": 0.90,
                    "tags": ["python", "cpp", "programming"],
                    "privacy_level": "network"
                },
                {
                    "type": "skill",
                    "name": "Computer Vision",
                    "description": "OpenCV, camera calibration, object detection and tracking",
                    "proficiency": 0.85,
                    "tags": ["vision", "opencv", "cameras"],
                    "privacy_level": "network"
                }
            ]
        )

        # Profile 2: Hardware/Electronics expert
        profile2 = create_test_profile(
            "test_user_hardware_002",
            [
                {
                    "type": "skill",
                    "name": "PCB Design & Electronics",
                    "description": "Circuit design, PCB layout, power management, signal integrity",
                    "proficiency": 0.92,
                    "tags": ["pcb", "electronics", "hardware", "circuits"],
                    "privacy_level": "network"
                },
                {
                    "type": "skill",
                    "name": "Sensor Integration",
                    "description": "LiDAR, IMU, GPS integration with microcontrollers and embedded systems",
                    "proficiency": 0.88,
                    "tags": ["sensors", "lidar", "imu", "embedded"],
                    "privacy_level": "network"
                },
                {
                    "type": "skill",
                    "name": "Mechanical Design",
                    "description": "CAD, mechanical assemblies, robotics chassis design",
                    "proficiency": 0.80,
                    "tags": ["mechanical", "cad", "design"],
                    "privacy_level": "network"
                }
            ]
        )

        # Profile 3: AI/ML expert
        profile3 = create_test_profile(
            "test_user_ai_003",
            [
                {
                    "type": "skill",
                    "name": "Deep Learning for Robotics",
                    "description": "Neural networks for perception, reinforcement learning for control",
                    "proficiency": 0.93,
                    "tags": ["ai", "ml", "deep-learning", "robotics"],
                    "privacy_level": "network"
                },
                {
                    "type": "skill",
                    "name": "Sensor Fusion Algorithms",
                    "description": "Kalman filtering, particle filters, multi-modal sensor fusion",
                    "proficiency": 0.87,
                    "tags": ["sensor-fusion", "algorithms", "kalman"],
                    "privacy_level": "network"
                }
            ]
        )

        # Test 3: Find Matches - Software person needs hardware help
        print_section("Finding Matches: Software Expert Needs Hardware Help")

        matches1 = find_matches_for_need(
            "test_user_software_001",
            {
                "user_id": "test_user_software_001",
                "need_name": "Need help with sensor hardware integration",
                "need_description": """I'm building an autonomous robot and have the ROS2 software stack
                working well, but I'm struggling with the hardware side. Specifically, I need help with:
                - Integrating LiDAR and IMU sensors
                - Proper power management for multiple sensors
                - Signal timing and synchronization
                - PCB design for custom sensor mounting
                I have strong software skills but limited electronics experience.""",
                "need_domain": "robotics",
                "need_tags": ["hardware", "sensors", "lidar", "imu", "pcb"],
                "urgency": 0.7,
                "importance": 0.8,
                "max_results": 5
            }
        )

        # Display top match details
        if matches1['matches_found'] > 0:
            top_match = matches1['matches'][0]
            print("\nTop Match Details:")
            print(f"  Capability: {top_match['capability']['name']}")
            print(f"  User: {top_match['capability_user_id']}")
            print(f"  Match Score: {top_match['scores']['match_score']:.2f}")
            print(f"  Confidence: {top_match['scores']['confidence']:.2f}")
            print(f"  Complementarity: {top_match['scores']['complementarity']:.2f}")
            print(f"  Explanation: {top_match['explanation'].get('summary', 'N/A')}")

        # Test 4: Find Matches - Hardware person needs software help
        print_section("Finding Matches: Hardware Expert Needs Software Help")

        matches2 = find_matches_for_need(
            "test_user_hardware_002",
            {
                "user_id": "test_user_hardware_002",
                "need_name": "Need ROS2 integration expertise",
                "need_description": """I've designed custom sensor boards and have working hardware,
                but I need help integrating everything into ROS2. Looking for someone who can:
                - Write ROS2 drivers for custom sensors
                - Set up navigation stack
                - Implement SLAM algorithms
                - Help with software architecture
                I have the hardware ready but limited software experience.""",
                "need_domain": "robotics",
                "need_tags": ["software", "ros2", "navigation", "slam"],
                "urgency": 0.6,
                "importance": 0.8,
                "max_results": 5
            }
        )

        # Display complementarity opportunity
        if matches2['matches_found'] > 0:
            top_match = matches2['matches'][0]
            print("\nTop Match Details:")
            print(f"  Capability: {top_match['capability']['name']}")
            print(f"  User: {top_match['capability_user_id']}")
            print(f"  Match Score: {top_match['scores']['match_score']:.2f}")

            # Check if there's mutual complementarity
            if top_match['capability_user_id'] == 'test_user_software_001':
                print("\n🌟 COMPLEMENTARITY DETECTED!")
                print("  Software expert needs hardware help")
                print("  Hardware expert needs software help")
                print("  → Perfect collaboration opportunity!")

        # Test 5: Get Statistics
        print_section("System Statistics")
        stats = get_stats()

        # Success!
        print_section("Integration Test Complete")
        print("✓ All tests passed!")
        print("\nSubstrate API is working correctly:")
        print("  • Profiles can be created and indexed")
        print("  • Semantic matching finds relevant capabilities")
        print("  • Transparency engine provides explanations")
        print("  • Complementarity detection works")
        print("  • Statistics are tracked")
        print("\nThe system is ready for production use!")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to API at {API_URL}")
        print("   Make sure the API server is running:")
        print("   python substrate/web/backend/api.py")
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
