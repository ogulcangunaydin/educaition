module.exports = {
  apps: [{
    name: 'educaition',
    script: './app/main.py'
  }],
  deploy: {
    production: {
      user: 'ec2-user',
      host: 'ec2-54-173-57-250.compute-1.amazonaws.com',
      key: '~/.ssh/id_rsa.pub',
      ref: 'origin/master',
      repo: 'git@github.com:ogulcangunaydin/educaition.git',
      path: '/home/ec2-user/educaition',
      'post-deploy': 'python3.10 -m venv env && pip install -r requirements.txt && uvicorn app.main:app --reload && pm2 startOrRestart ecosystem.config.js'
    }
  }
}
