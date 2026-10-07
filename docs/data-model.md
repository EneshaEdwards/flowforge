# FlowForge Data Model

DynamoDB, on-demand billing (PAY_PER_REQUEST). Two tables.

## Table 1: flowforge-poses (the pose library)

Partition key: `pose_id` (String)

| Attribute | Type | Example |
|---|---|---|
| pose_id | String | "pigeon" |
| name | String | "Pigeon Pose" |
| target_area | String | "hips" |
| difficulty | String | "intermediate" |
| hold_seconds | Number | 60 |

Example item:

```json
{
  "pose_id": "pigeon",
  "name": "Pigeon Pose",
  "target_area": "hips",
  "difficulty": "intermediate",
  "hold_seconds": 60
}
```

## Table 2: flowforge-flows (generated flows)

Partition key: `flow_id` (String)

| Attribute | Type | Example |
|---|---|---|
| flow_id | String | "flow-2026-10-07-001" |
| created_at | String | "2026-10-07T13:00:00Z" |
| target_area | String | "hips" |
| difficulty | String | "beginner" |
| pose_ids | List | ["child", "pigeon", "frog"] |

## Design decisions

- Two tables: poses are a fixed library, flows are created over time. They change at different rates.
- Readable pose_id values ("pigeon") instead of random IDs, so items are easy to debug.
- flows stores pose_ids, not full pose copies, so a pose is edited in one place.
- On-demand billing: no capacity to manage, and cost stays near zero at low traffic.
- Finding poses by target_area: a scan is fine at this size. A secondary index is the later upgrade.
- No user accounts in V1. Out of scope.
