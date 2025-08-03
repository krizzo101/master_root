# FILE_MAP_BEGIN {"file_metadata":{"type":"python","language":"python","title":"k6_performance_test.js","description":"Python module with 0 functions and 0 classes","last_updated":"2025-07-31"},"code_elements":{"functions":[],"classes":[],"imports":[],"constants":[]},"key_elements":[],"sections":[],"content_hash":"f23f137b9f5f7882efe3ede0a6b5c580"} FILE_MAP_END

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 250 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<250'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const response = http.get('http://localhost:8000/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 250ms': (r) => r.timings.duration < 250,
  });
  sleep(1);
}