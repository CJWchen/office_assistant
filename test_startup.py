#!/usr/bin/env python3
"""
应用启动测试
"""

import sys
import time
import threading
import requests
from app import create_app

def run_app():
    """运行Flask应用"""
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def test_app():
    """测试应用基本功能"""
    print("开始测试应用启动...")
    
    # 在后台启动应用
    server_thread = threading.Thread(target=run_app, daemon=True)
    server_thread.start()
    
    # 等待应用启动
    time.sleep(2)
    
    try:
        # 测试状态接口
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态接口正常: {data}")
        else:
            print(f"❌ 状态接口异常: {response.status_code}")
            return False
        
        # 测试首页
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code == 200:
            print("✅ 首页访问正常")
        else:
            print(f"❌ 首页访问异常: {response.status_code}")
            return False
        
        print("✅ 所有测试通过！")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到应用服务器")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False
    finally:
        # 应用会在主线程退出时停止（因为是守护线程）
        pass

if __name__ == '__main__':
    success = test_app()
    sys.exit(0 if success else 1)