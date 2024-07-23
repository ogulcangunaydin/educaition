module.exports = {
  apps: [{
    name: 'educaition',
    script: 'uvicorn',
    interpreter: '~/educaition/source/env/bin/python3.10',
    args: 'app.main:app --port 80',
  }],
  deploy: {
    production: {
      user: 'ec2-user',
      host: 'ec2-54-173-57-250.compute-1.amazonaws.com',
      key: '~/.ssh/id_rsa.pub',
      ref: 'origin/master',
      repo: 'git@github.com:ogulcangunaydin/educaition.git',
      path: '/home/ec2-user/educaition/source',
      'post-deploy': 'python3.10 -m venv env && pip install -r requirements.txt && pm2 startOrRestart ecosystem.config.js'
    }
  }
}
