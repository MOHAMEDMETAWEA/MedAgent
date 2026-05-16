import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 }, // Simulate ramp-up of traffic from 1 to 20 users over 30s.
    { duration: '1m', target: 20 },  // Stay at 20 users for 1 minute.
    { duration: '10s', target: 0 },  // Ramp-down to 0 users.
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.01'],   // Error rate should be less than 1%
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';

export default function () {
  // Test Health Endpoint
  const healthRes = http.get(`${BASE_URL}/docs`);
  
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });

  // Attempt to hit the conversation API without auth (should return 401, but validates routing speed)
  const convRes = http.get(`${BASE_URL}/api/v1/conversations`);
  check(convRes, {
    'conversations requires auth': (r) => r.status === 401 || r.status === 403,
  });

  sleep(1);
}
