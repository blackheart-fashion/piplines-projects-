// Local automation only: secrets are mounted from ignored .local-jenkins files.
import jenkins.model.Jenkins
import jenkins.model.JenkinsLocationConfiguration
import hudson.model.Node
import hudson.model.User
import hudson.slaves.DumbSlave
import hudson.slaves.JNLPLauncher
import hudson.slaves.RetentionStrategy
import hudson.security.HudsonPrivateSecurityRealm
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import hudson.plugins.git.GitSCM
import hudson.plugins.git.UserRemoteConfig
import hudson.plugins.git.BranchSpec

def instance = Jenkins.get()
def secrets = new File('/run/workshop-secrets')
if (!new File(secrets, 'admin-password').exists()) {
    println('Workshop initialization skipped: no local secrets supplied.')
    return
}
def realm = new HudsonPrivateSecurityRealm(false)
realm.createAccount('workshop-admin', new File(secrets, 'admin-password').text.trim())
instance.setSecurityRealm(realm)
def authorization = new FullControlOnceLoggedInAuthorizationStrategy()
authorization.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(authorization)
instance.setNumExecutors(0)
JenkinsLocationConfiguration.get().setUrl('http://127.0.0.1:8080/')
instance.save()

def store = SystemCredentialsProvider.getInstance().getStore()
def domain = Domain.global()
def tokenFile = new File(secrets, 'github-token')
if (tokenFile.exists()) {
    def credential = new UsernamePasswordCredentialsImpl(
        CredentialsScope.GLOBAL, 'github-read', 'Local workshop GitHub checkout',
        new File(secrets, 'github-user').text.trim(), tokenFile.text.trim())
    def old = store.getCredentials(domain).find { it.id == 'github-read' }
    if (old) { store.updateCredentials(domain, old, credential) }
    else { store.addCredentials(domain, credential) }
}
if (instance.getNode('workshop-agent') == null) {
    def node = new DumbSlave('workshop-agent', '/home/jenkins/agent', new JNLPLauncher())
    node.setNumExecutors(1)
    node.setLabelString('workshop-linux')
    node.setMode(Node.Mode.EXCLUSIVE)
    node.setRetentionStrategy(new RetentionStrategy.Always())
    instance.addNode(node)
}
def agent = instance.getNode('workshop-agent')
new File(secrets, 'agent-secret').text = agent.toComputer().getJnlpMac()

def repo = new File(secrets, 'repo-url').text.trim()
['day1', 'day2'].each { day ->
    def name = "workshop-${day}"
    def job = instance.getItem(name) ?: instance.createProject(WorkflowJob, name)
    def scm = new GitSCM(
        [new UserRemoteConfig(repo, null, null, 'github-read')],
        [new BranchSpec('*/main')], false, [], null, null, [])
    job.setDefinition(new CpsScmFlowDefinition(scm, "pipelines/Jenkinsfile.${day}"))
    job.save()
}
println('Workshop controller configured: authenticated access, zero controller executors, two jobs.')
