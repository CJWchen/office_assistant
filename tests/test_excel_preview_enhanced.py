#!/usr/bin/env python3
"""
测试增强版Excel预览API
"""

import os
import sys
import tempfile
import pandas as pd
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.models import Upload, User, db


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_excel_file():
    """创建测试Excel文件"""
    # 创建测试数据
    data = {
        'Name': ['Alice', 'Bob', 'Charlie', None, 'Eve'],
        'Age': [30, 25, 35, None, 32],
        'Salary': [75000.0, 65000.5, 80000.0, None, 72000.0],
        'Department': ['Engineering', 'Sales', 'Engineering', None, 'HR']
    }
    df = pd.DataFrame(data)
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df.to_excel(f.name, index=False, engine='openpyxl')
        filepath = f.name
    
    yield filepath
    
    # 清理
    os.unlink(filepath)


@pytest.fixture
def test_csv_file():
    """创建测试CSV文件"""
    data = {
        'Product': ['Laptop', 'Mouse', 'Keyboard'],
        'Price': [1200.0, 25.5, 80.0],
        'Quantity': [10, 50, 30]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        filepath = f.name
    
    yield filepath
    os.unlink(filepath)


class TestExcelPreviewEnhanced:
    """测试增强版Excel预览API"""
    
    def test_api_response_structure(self, app, client, test_user, test_excel_file):
        """测试API响应结构"""
        with app.app_context():
            # 创建上传记录
            upload = Upload(
                filename='test.xlsx',
                upload_path=test_excel_file,
                user_id=test_user.id
            )
            db.session.add(upload)
            db.session.commit()
            
            # 模拟用户登录
            with client.session_transaction() as session:
                session['_user_id'] = str(test_user.id)
            
            # 调用API
            response = client.get(f'/api/excel/preview/{upload.id}')
            data = response.json()
            
            # 验证响应结构
            assert response.status_code == 200
            assert data['success'] == True
            assert 'data' in data
            assert 'stats' in data
            
            # 验证stats结构
            stats = data['stats']
            required_keys = ['row_count', 'column_count', 'data_types', 
                           'missing_values_total', 'missing_values_by_column',
                           'numeric_stats', 'preprocessing']
            for key in required_keys:
                assert key in stats, f"Missing key in stats: {key}"
    
    def test_stats_calculation(self, app, client, test_user, test_excel_file):
        """测试统计信息计算"""
        with app.app_context():
            upload = Upload(
                filename='test.xlsx',
                upload_path=test_excel_file,
                user_id=test_user.id
            )
            db.session.add(upload)
            db.session.commit()
            
            with client.session_transaction() as session:
                session['_user_id'] = str(test_user.id)
            
            response = client.get(f'/api/excel/preview/{upload.id}')
            data = response.json()
            
            # 验证基本维度
            stats = data['stats']
            assert stats['row_count'] == 5  # 包含空行
            assert stats['column_count'] == 4
            
            # 验证缺失值统计
            assert stats['missing_values_total'] >= 0
            assert 'Name' in stats['missing_values_by_column']
            
            # 验证数值列统计
            numeric_stats = stats['numeric_stats']
            assert 'Age' in numeric_stats
            assert 'Salary' in numeric_stats
            
            # 验证数值统计包含基本统计量
            age_stats = numeric_stats['Age']
            required_stats = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
            for stat in required_stats:
                assert stat in age_stats
    
    def test_csv_file_support(self, app, client, test_user, test_csv_file):
        """测试CSV文件支持"""
        with app.app_context():
            upload = Upload(
                filename='test.csv',
                upload_path=test_csv_file,
                user_id=test_user.id
            )
            db.session.add(upload)
            db.session.commit()
            
            with client.session_transaction() as session:
                session['_user_id'] = str(test_user.id)
            
            response = client.get(f'/api/excel/preview/{upload.id}')
            data = response.json()
            
            assert response.status_code == 200
            assert data['success'] == True
            assert len(data['data']) > 0
    
    def test_error_handling_invalid_format(self, app, client, test_user):
        """测试不支持文件格式的错误处理"""
        # 创建不支持的格式文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'PDF content')
            filepath = f.name
        
        try:
            with app.app_context():
                upload = Upload(
                    filename='test.pdf',
                    upload_path=filepath,
                    user_id=test_user.id
                )
                db.session.add(upload)
                db.session.commit()
                
                with client.session_transaction() as session:
                    session['_user_id'] = str(test_user.id)
                
                response = client.get(f'/api/excel/preview/{upload.id}')
                data = response.json()
                
                # 应该返回400错误
                assert response.status_code == 400
                assert data['success'] == False
                assert '不支持的文件格式' in data['message']
        finally:
            os.unlink(filepath)
    
    def test_error_handling_file_not_found(self, app, client, test_user):
        """测试文件不存在的错误处理"""
        with app.app_context():
            # 创建记录但文件实际不存在
            upload = Upload(
                filename='missing.xlsx',
                upload_path='/path/to/nonexistent/file.xlsx',
                user_id=test_user.id
            )
            db.session.add(upload)
            db.session.commit()
            
            with client.session_transaction() as session:
                session['_user_id'] = str(test_user.id)
            
            response = client.get(f'/api/excel/preview/{upload.id}')
            data = response.json()
            
            assert response.status_code == 404
            assert data['success'] == False
            assert '文件不存在于服务器' in data['message']
    
    def test_data_preprocessing(self, app, client, test_user):
        """测试数据预处理功能"""
        # 创建包含空行空列的Excel文件
        import numpy as np
        data = {
            'Col1': [1, 2, np.nan, np.nan],
            'Col2': [np.nan, np.nan, np.nan, np.nan],  # 全空列
            'Col3': ['A', 'B', np.nan, 'D']
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            df.to_excel(f.name, index=False, engine='openpyxl')
            filepath = f.name
        
        try:
            with app.app_context():
                upload = Upload(
                    filename='test_empty.xlsx',
                    upload_path=filepath,
                    user_id=test_user.id
                )
                db.session.add(upload)
                db.session.commit()
                
                with client.session_transaction() as session:
                    session['_user_id'] = str(test_user.id)
                
                response = client.get(f'/api/excel/preview/{upload.id}')
                data = response.json()
                
                # 验证预处理信息
                preprocessing = data['stats']['preprocessing']
                assert preprocessing['removed_empty_columns'] == 1  # 删除了全空列
                assert preprocessing['cleaned_shape'][1] == 2  # 处理后列数为2
        finally:
            os.unlink(filepath)
    
    def test_backward_compatibility(self, app, client, test_user, test_excel_file):
        """测试向后兼容性"""
        with app.app_context():
            upload = Upload(
                filename='test.xlsx',
                upload_path=test_excel_file,
                user_id=test_user.id
            )
            db.session.add(upload)
            db.session.commit()
            
            with client.session_transaction() as session:
                session['_user_id'] = str(test_user.id)
            
            response = client.get(f'/api/excel/preview/{upload.id}')
            data = response.json()
            
            # 原有基础API功能仍然正常工作
            assert response.status_code == 200
            assert data['success'] == True
            assert 'data' in data
            # 数据预览功能正常
            assert isinstance(data['data'], list)
            if len(data['data']) > 0:
                assert isinstance(data['data'][0], dict)


if __name__ == '__main__':
    # 简单运行测试（需要pytest）
    import sys
    sys.exit(pytest.main([__file__, '-v']))