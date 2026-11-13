#if CYTOID_NATIVE_AUDIO
using UnityEngine;

/// <summary>
/// Hybrid audio server: Unity for music (scheduling + clock), NativeAudio for SFX (low latency).
/// Uses COMPOSITION — holds a private UnityAudioServer and NativeSfxBackend, NOT inheritance.
/// </summary>
public class Exceed7AudioServer : IAudioServer
{
    private readonly UnityAudioServer _unity;
    private readonly NativeSfxBackend _native;

    public Exceed7AudioServer(AudioSource musicSource, AudioSource[] sfxPool)
    {
        _unity = new UnityAudioServer(musicSource, sfxPool);
        _native = new NativeSfxBackend();
    }

    public void Initialize()
    {
        _unity.Initialize();
        _native.Initialize();
    }

    public void Dispose()
    {
        // Reverse order: native first (release native sources), then Unity
        _native.Dispose();
        _unity.Dispose();
    }

    // Music: delegate to Unity (Unity is ALWAYS the music backend, even in Exceed7)
    public IMusicTrack LoadMusic(string id, AudioClip clip, bool isResource)
        => _unity.LoadMusic(id, clip, isResource);

    public void UnloadMusic() => _unity.UnloadMusic();
    public void SetMusicVolume(float volume) => _unity.SetMusicVolume(volume);

    // SFX: delegate to Native
    public ISoundEffect LoadSfx(string id, AudioClip clip, bool isResource, bool isPreloaded = false)
        => _native.LoadSfx(id, clip, isResource, isPreloaded);

    public ISoundEffect GetSfx(string id) => _native.GetSfx(id);
    public void UnloadSfx(string id) => _native.UnloadSfx(id);
    public bool IsSfxLoaded(string id) => _native.IsSfxLoaded(id);
    public void SetSfxVolume(float volume) => _native.SetSfxVolume(volume);

    // Both
    public void UpdateVolumes(float musicVolume, float sfxVolume)
    {
        _unity.SetMusicVolume(musicVolume);
        _native.SetSfxVolume(sfxVolume);
    }

    // HARD INVARIANT: Unity is always the music clock, even in Exceed7
    public double AudioClockSeconds => _unity.AudioClockSeconds;
}
#else
using UnityEngine;

/// <summary>
/// Compatibility fallback for builds without the optional Native Audio package.
/// AudioManager normally selects UnityAudioServer before this type is constructed,
/// but retaining a complete Unity implementation keeps the enum and host protocol
/// stable for callers that explicitly request Exceed7.
/// </summary>
public class Exceed7AudioServer : IAudioServer
{
    private readonly UnityAudioServer _fallback;

    public Exceed7AudioServer(AudioSource musicSource, AudioSource[] sfxPool)
    {
        _fallback = new UnityAudioServer(musicSource, sfxPool);
    }

    public void Initialize() => _fallback.Initialize();
    public void Dispose() => _fallback.Dispose();
    public IMusicTrack LoadMusic(string id, AudioClip clip, bool isResource)
        => _fallback.LoadMusic(id, clip, isResource);
    public void UnloadMusic() => _fallback.UnloadMusic();
    public void SetMusicVolume(float volume) => _fallback.SetMusicVolume(volume);
    public ISoundEffect LoadSfx(string id, AudioClip clip, bool isResource, bool isPreloaded = false)
        => _fallback.LoadSfx(id, clip, isResource, isPreloaded);
    public ISoundEffect GetSfx(string id) => _fallback.GetSfx(id);
    public void UnloadSfx(string id) => _fallback.UnloadSfx(id);
    public bool IsSfxLoaded(string id) => _fallback.IsSfxLoaded(id);
    public void SetSfxVolume(float volume) => _fallback.SetSfxVolume(volume);
    public void UpdateVolumes(float musicVolume, float sfxVolume)
        => _fallback.UpdateVolumes(musicVolume, sfxVolume);
    public double AudioClockSeconds => _fallback.AudioClockSeconds;
}
#endif
