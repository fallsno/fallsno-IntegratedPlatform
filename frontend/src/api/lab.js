import axios from 'axios'

const labApi = axios.create({
  baseURL: '/lab-api'
})

export default labApi
