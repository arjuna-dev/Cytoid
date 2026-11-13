using NUnit.Framework;
using Kiirtaniyas.Visual;
using UnityEngine;

public sealed class KiirtanVisualTimelineTests
{
    [Test]
    public void DefaultTimelineMovesThroughAllStages()
    {
        var timeline = new KiirtanStageTimeline();

        Assert.AreEqual(KiirtanStage.Intimate, timeline.Evaluate(0f));
        Assert.AreEqual(KiirtanStage.Heavenly, timeline.Evaluate(52.5f));
        Assert.AreEqual(KiirtanStage.CosmicSpace, timeline.Evaluate(105f));
        Assert.AreEqual(KiirtanStage.CosmicFractal, timeline.Evaluate(157.5f));
        Assert.AreEqual(KiirtanStage.SoloCosmic, timeline.Evaluate(199.5f));
    }

    [Test]
    public void TimelineClampsOutsideSongBounds()
    {
        var timeline = new KiirtanStageTimeline();

        Assert.AreEqual(KiirtanStage.Intimate, timeline.Evaluate(-10f));
        Assert.AreEqual(KiirtanStage.SoloCosmic, timeline.Evaluate(999f));
        Assert.That(timeline.GetStageProgress(-1f), Is.EqualTo(0f).Within(0.0001f));
        Assert.That(timeline.GetStageProgress(999f), Is.EqualTo(1f).Within(0.0001f));
    }

    [Test]
    public void TimelineReportsStageStartInSeconds()
    {
        var timeline = new KiirtanStageTimeline();

        Assert.That(
            timeline.GetStageStartSeconds(KiirtanStage.CosmicFractal),
            Is.EqualTo(157.5f).Within(0.0001f));
        Assert.AreEqual(-1f, timeline.GetStageStartSeconds((KiirtanStage)99));
    }

    [Test]
    public void OrbitActorKeepsClockwisePhaseAtTheConfiguredRadius()
    {
        GameObject centerObject = new GameObject("Kiirtan test center");
        GameObject actorObject = new GameObject("Kiirtan test actor");
        try
        {
            KiirtanOrbitActor actor = actorObject.AddComponent<KiirtanOrbitActor>();
            actor.Radius = 2f;
            actor.SetOrbitCenter(centerObject.transform);
            actor.SetPhase(90f);

            Assert.IsTrue(actor.Clockwise);
            Assert.That(actor.transform.position.x, Is.EqualTo(0f).Within(0.0001f));
            Assert.That(actor.transform.position.z, Is.EqualTo(2f).Within(0.0001f));
        }
        finally
        {
            Object.DestroyImmediate(actorObject);
            Object.DestroyImmediate(centerObject);
        }
    }
}
