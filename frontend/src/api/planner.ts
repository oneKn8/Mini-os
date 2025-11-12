import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export interface TodayPlan {
  must_do_today: string[]
  focus_areas: string[]
  time_recommendations: Array<{
    task: string
    suggested_time: string
    duration_minutes: number
  }>
}

export async function fetchTodayPlan(): Promise<TodayPlan> {
  const response = await api.get('/planner/today')
  return response.data
}

