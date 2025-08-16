import React from 'react';
import ExcelUpload from '../components/ExcelUpload';
import Layout from '../components/Layout';

const ExcelUploadPage = () => {
  return (
    <Layout>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <ExcelUpload />
      </div>
    </Layout>
  );
};

export default ExcelUploadPage;
