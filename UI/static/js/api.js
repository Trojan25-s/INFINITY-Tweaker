/**
 * INFINITY Tweaker Client API Connector
 */
const API = {
    async getAuthStatus() {
        const res = await fetch('/api/client/auth/status');
        return res.json();
    },

    async activateLicense(code) {
        const res = await fetch('/api/client/auth/activate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({code})
        });
        return res.json();
    },

    async deactivate() {
        const res = await fetch('/api/client/auth/deactivate', {method: 'POST'});
        return res.json();
    },

    async getDashboardOverview() {
        const res = await fetch('/api/client/dashboard/overview');
        return res.json();
    },

    async getSystemInfo() {
        const res = await fetch('/api/client/system/info');
        return res.json();
    },

    async optimizeRam() {
        const res = await fetch('/api/client/optimize/ram', {method: 'POST'});
        return res.json();
    },

    async scanCaches() {
        const res = await fetch('/api/client/cache/scan');
        return res.json();
    },

    async cleanAllCaches() {
        const res = await fetch('/api/client/cache/clean', {method: 'POST'});
        return res.json();
    },

    async cleanCategoryCache(category) {
        const res = await fetch(`/api/client/cache/clean/${category}`, {method: 'POST'});
        return res.json();
    },

    async getWindowsTweaks() {
        const res = await fetch('/api/client/windows/tweaks');
        return res.json();
    },

    async applyTweak(tweak_id, enable) {
        const res = await fetch('/api/client/windows/tweaks/apply', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({tweak_id, enable})
        });
        return res.json();
    },

    async getPowerPlans() {
        const res = await fetch('/api/client/power/plans');
        return res.json();
    },

    async setPowerPlan(plan_name) {
        const res = await fetch('/api/client/power/set', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({plan_name})
        });
        return res.json();
    },

    async getServices() {
        const res = await fetch('/api/client/services');
        return res.json();
    },

    async changeServiceStartup(service_name, startup_type) {
        const res = await fetch('/api/client/services/startup', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({service_name, startup_type})
        });
        return res.json();
    },

    async getStartupItems() {
        const res = await fetch('/api/client/startup');
        return res.json();
    },

    async toggleStartupItem(name, enable) {
        const res = await fetch('/api/client/startup/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, enable})
        });
        return res.json();
    },

    async runNetworkDiagnostic() {
        const res = await fetch('/api/client/network/diagnostic');
        return res.json();
    },

    async getLargeFiles() {
        const res = await fetch('/api/client/storage/large-files');
        return res.json();
    },

    async getGpuStatus() {
        const res = await fetch('/api/client/gpu/status');
        return res.json();
    },

    async getDetectedGames() {
        const res = await fetch('/api/client/games/detected');
        return res.json();
    },

    async getGameProfiles() {
        const res = await fetch('/api/client/games/profiles');
        return res.json();
    },

    async launchGame(profile_id) {
        const res = await fetch('/api/client/games/launch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({profile_id})
        });
        return res.json();
    },

    async runBenchmark(stage = "CURRENT") {
        const res = await fetch(`/api/client/benchmark/run?stage=${stage}`, {method: 'POST'});
        return res.json();
    },

    async getAIRecommendations() {
        const res = await fetch('/api/client/ai/recommendations');
        return res.json();
    },

    async queryAIAssistant(question) {
        const res = await fetch('/api/client/ai/query', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question})
        });
        return res.json();
    },

    async getChangeHistory() {
        const res = await fetch('/api/client/history/changes');
        return res.json();
    },

    async getSnapshots() {
        const res = await fetch('/api/client/backup/snapshots');
        return res.json();
    },

    async createSnapshot(name) {
        const res = await fetch(`/api/client/backup/create?name=${encodeURIComponent(name)}`, {method: 'POST'});
        return res.json();
    }
};
