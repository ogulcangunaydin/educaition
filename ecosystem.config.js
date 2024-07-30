module.exports = {
  apps: [{
    name: 'educaition',
    script: 'uvicorn',
    interpreter: 'python3.10',
    args: 'app.main:app --port 3000',
  }],
  deploy: {
    production: {
      user: 'ec2-user',
      host: 'ec2-54-173-57-250.compute-1.amazonaws.com',
      key: '~/.ssh/educaition-key-pair.pem',
      ref: 'origin/main',
      repo: 'git@github.com:ogulcangunaydin/educaition.git',
      path: '/home/ec2-user/educaition',
      'post-deploy': 'python3.10 -m venv env && source env/bin/activate && pip install -r requirements.txt && alembic upgrade head && /usr/bin/pm2 startOrRestart ecosystem.config.js'
    }
  }
}
