#!/usr/bin/env python3
"""
Test the new bidirectional connect-nodes endpoint
"""

import requests
import json

def test_new_endpoint():
    """Test the new /api/connect-nodes endpoint"""
    
    try:
        # Test data
        data = {
            'nodes': ['left radial artery', 'right radial artery']
        }
        
        print("🔍 Testing new /api/connect-nodes endpoint...")
        print(f"🎯 Connecting: {data['nodes']}")
        print("=" * 60)
        
        response = requests.post('http://localhost:5000/api/connect-nodes', 
                               headers={'Content-Type': 'application/json'},
                               json=data,
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print('🎉 SUCCESS: Bidirectional connection found!')
            print(f"✅ Found: {result.get('found', False)}")
            print(f"📊 Total nodes: {len(result.get('nodes', []))}")
            print(f"🔗 Total links: {len(result.get('links', []))}")
            print(f"🔧 Algorithm: {result.get('algorithm', 'unknown')}")
            print(f"📝 Message: {result.get('message', '')}")
            
            # Check for aortic arch
            nodes = result.get('nodes', [])
            aortic_found = False
            
            print(f"\n🔍 Searching for aortic arch...")
            for node in nodes:
                name = node.get('properties', {}).get('name', node.get('name', 'Unknown'))
                if 'aortic' in name.lower() or 'arch' in name.lower():
                    color = node.get('color', 'unknown')
                    is_source = node.get('isSource', False)
                    role = "🟠 SOURCE" if is_source else "🔵 CONNECTOR"
                    print(f"🎯 FOUND AORTIC: {name} ({role})")
                    aortic_found = True
            
            if not aortic_found:
                print("❌ No aortic arch found in results")
            
            # Show first 15 nodes
            print(f"\n📋 CONNECTION PATH (first 15 nodes):")
            print("-" * 50)
            for i, node in enumerate(nodes[:15]):
                name = node.get('properties', {}).get('name', node.get('name', 'Unknown'))
                labels = ', '.join(node.get('labels', []))
                color = node.get('color', 'default')
                is_source = node.get('isSource', False)
                role = "🟠 SOURCE" if is_source else "🔵 PATH"
                
                print(f"  {i+1:2d}. {name} ({labels}) - {role}")
                
            return {
                "success": True,
                "total_nodes": len(nodes),
                "aortic_found": aortic_found
            }
            
        else:
            print(f'❌ ERROR: HTTP {response.status_code}')
            print(response.text)
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f'💥 ERROR: {e}')
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # First check if server is running
    try:
        test_response = requests.get('http://localhost:5000/api/labels', timeout=5)
        if test_response.status_code == 200:
            print("✅ Server is running")
            result = test_new_endpoint()
            print(f"\n📋 FINAL RESULT: {json.dumps(result, indent=2)}")
        else:
            print("❌ Server not responding properly")
    except:
        print("❌ Server not running - please start with: python app.py")