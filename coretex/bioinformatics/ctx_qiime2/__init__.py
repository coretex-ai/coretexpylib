#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Union
from pathlib import Path

import os

from .utils import compressGzip, createSample, getDemuxSamples, getDenoisedSamples, \
    getFastqDPSamples, getFastqMPSamples, getImportedSamples, getMetadata, getPhylogeneticTreeSamples, \
    isDemultiplexedSample, isDenoisedSample, isFastqDPSample, isFastqMPSample, \
    isImportedSample, isPhylogeneticTreeSample, sampleNumber, isPairedEnd

from ...utils import command


def toolsImport(
    sequenceType: str,
    inputPath: str,
    outputPath: str,
    inputFormat: Optional[str] = None
) -> None:

    args = [
        "qiime", "tools", "import",
        "--type", sequenceType,
        "--input-path", str(inputPath),
        "--output-path", str(outputPath)
    ]

    if inputFormat is not None:
        args.extend([
            "--input-format" , inputFormat
        ])

    command(args)


def demuxEmpSingle(
    sequencesPath: str,
    barcodesPath: str,
    barcodesColumn: str,
    perSampleSequences: str,
    errorCorretctionDetailsPath: str
) -> None:

    command([
        "qiime", "demux", "emp-single",
        "--i-seqs", sequencesPath,
        "--m-barcodes-file", barcodesPath,
        "--m-barcodes-column", barcodesColumn,
        "--o-per-sample-sequences", perSampleSequences,
        "--o-error-correction-details", errorCorretctionDetailsPath,
        "--verbose"
    ])


def demuxEmpPaired(
    sequencesPath: Union[str, Path],
    barcodesPath: Union[str, Path],
    barcodesColumn: str,
    perSampleSequences: Union[str, Path],
    errorCorretctionDetailsPath: Union[str, Path]
) -> None:
    """
        Wrapper for QIIME's demux emp-paired command, which performs demultiplexing of multiplexed
        sequences in the Earth Microbiome Project amplicon sequencing standard format
        http://www.earthmicrobiome.org/protocols-and-standards/.

        Parameters
        ----------
        sequencesPath : Union[str, Path]
            Path to the paired-end demultiplexed sequences to be denoised
        barcodesPath : Union[str, Path]
            Output path to the resulting feature sequences
        perSampleSequences : Union[str, Path]
            Output path to the resulting feature table
        errorCorretctionDetailsPath : Union[str, Path]
            Output path to the statistics of the denoising
    """

    if isinstance(sequencesPath, Path):
        sequencesPath = str(sequencesPath)

    if isinstance(barcodesPath, Path):
        barcodesPath = str(barcodesPath)

    if isinstance(perSampleSequences, Path):
        perSampleSequences = str(perSampleSequences)

    if isinstance(errorCorretctionDetailsPath, Path):
        errorCorretctionDetailsPath = str(errorCorretctionDetailsPath)

    command([
        "qiime", "demux", "emp-paired",
        "--i-seqs", sequencesPath,
        "--m-barcodes-file", barcodesPath,
        "--m-barcodes-column", barcodesColumn,
        "--o-per-sample-sequences", perSampleSequences,
        "--o-error-correction-details", errorCorretctionDetailsPath,
        "--verbose"
    ])


def demuxSummarize(dataPath: str, visualizationPath: str) -> None:
    command([
        "qiime", "demux", "summarize",
        "--i-data", dataPath,
        "--o-visualization", visualizationPath
    ])


def dada2DenoiseSingle(
    inputPath: Union[str, Path],
    trimLeft: int,
    truncLen: int,
    representativeSequencesPath: Union[str, Path],
    tablePath: Union[str, Path],
    denoisingStatsPath: Union[str, Path],
    threads: Optional[int] = -1
) -> None:
    """
        Wrapper for QIIME's DADA2 denoise-single, which performs denoising on the input paired-end reads.

        Parameters
        ----------
        inputPath : Union[str, Path]
            Path to the paired-end demultiplexed sequences to be denoised
        trimLeft : int
            Position at which read sequences should be trimmed due to low quality.
            This trims the 5' end of the input sequences, which will be the bases that were
            sequenced in the first cycles
        truncLen : int
            Position at which read sequences should be truncated due to decrease in quality.
            This truncates the 3' end of the input sequences, which will be the bases that
            were sequenced in the last cycles. Reads that are shorter than this value will be discarded.
            After this parameter is applied there must still be at least a 20 nucleotide overlap
            between the forward and reverse reads. If 0 is provided, no truncation or length
            filtering will be performed
        representativeSequencesPath : Union[str, Path]
            Output path to the resulting feature sequences. Each feature in the feature table will
            be represented by exactly one sequence, and these sequences will be the
            joined paired-end sequences
        tablePath : Union[str, Path]
            Output path to the resulting feature table
        denoisingStatsPath : Union[str, Path]
            Output path to the statistics of the denoising
        threads : Optional[int]
            Number of threads to use for the process. If None, multithreading will not be used.
            Set to -1 (defaul) to use a thread for each CPU core
    """

    if isinstance(inputPath, Path):
        inputPath = str(inputPath)

    if isinstance(representativeSequencesPath, Path):
        representativeSequencesPath = str(representativeSequencesPath)

    if isinstance(tablePath, Path):
        tablePath = str(tablePath)

    if isinstance(denoisingStatsPath, Path):
        denoisingStatsPath = str(denoisingStatsPath)

    args = [
        "qiime", "dada2", "denoise-single",
        "--i-demultiplexed-seqs", inputPath,
        "--p-trim-left", str(trimLeft),
        "--p-trunc-len", str(truncLen),
        "--o-representative-sequences", representativeSequencesPath,
        "--o-table", tablePath,
        "--o-denoising-stats", denoisingStatsPath
    ]

    if threads == -1:
        args.extend(["--p-n-threads", "0"])
    elif threads is not None:
        args.extend(["--p-n-threads", str()])

    command(args)


def dada2DenoisePaired(
    inputPath: Union[str, Path],
    trimLeftF: int,
    trimLeftR: int,
    truncLenF: int,
    truncLenR: int,
    representativeSequencesPath: Union[str, Path],
    tablePath: Union[str, Path],
    denoisingStatsPath: Union[str, Path],
    threads: Optional[int] = -1
) -> None:
    """
        Wrapper for QIIME's DADA2 denoise-paired, which performs denoising on the input paired-end reads.

        Parameters
        ----------
        inputPath : Union[str, Path]
            Path to the paired-end demultiplexed sequences to be denoised
        trimLeftF : int
            Position at which forward read sequences should be trimmed due to low quality.
            This trims the 5' end of the input sequences, which will be the bases that were
            sequenced in the first cycles
        trimLeftR : int
            Position at which reverse read sequences should be trimmed due to low quality.
            This trims the 5' end of the input sequences, which will be the bases that were
            sequenced in the first cycles
        truncLenF : int
            Position at which forward read sequences should be truncated due to decrease in quality.
            This truncates the 3' end of the input sequences, which will be the bases that
            were sequenced in the last cycles. Reads that are shorter than this value will be discarded.
            After this parameter is applied there must still be at least a 20 nucleotide overlap
            between the forward and reverse reads. If 0 is provided, no truncation or length
            filtering will be performed
        truncLenR : int
            Position at which reverse read sequences should be truncated due to decrease in quality.
            This truncates the 3' end of the input sequences, which will be the bases that
            were sequenced in the last cycles. Reads that are shorter than this value will be discarded.
            After this parameter is applied there must still be at least a 20 nucleotide overlap
            between the forward and reverse reads. If 0 is provided, no truncation or length
            filtering will be performed
        representativeSequencesPath : Union[str, Path]
            Output path to the resulting feature sequences. Each feature in the feature table will
            be represented by exactly one sequence, and these sequences will be the
            joined paired-end sequences
        tablePath : Union[str, Path]
            Output path to the resulting feature table
        denoisingStatsPath : Union[str, Path]
            Output path to the statistics of the denoising
        threads : Optional[int]
            Number of threads to use for the process. If None, multithreading will not be used.
            Set to -1 (defaul) to use a thread for each CPU core
    """

    if isinstance(inputPath, Path):
        inputPath = str(inputPath)

    if isinstance(representativeSequencesPath, Path):
        representativeSequencesPath = str(representativeSequencesPath)

    if isinstance(tablePath, Path):
        tablePath = str(tablePath)

    if isinstance(denoisingStatsPath, Path):
        denoisingStatsPath = str(denoisingStatsPath)

    args = [
        "qiime", "dada2", "denoise-paired",
        "--i-demultiplexed-seqs", inputPath,
        "--p-trim-left-f", str(trimLeftF),
        "--p-trim-left-r", str(trimLeftR),
        "--p-trunc-len-f", str(truncLenF),
        "--p-trunc-len-r", str(truncLenR),
        "--o-representative-sequences", representativeSequencesPath,
        "--o-table", tablePath,
        "--o-denoising-stats", denoisingStatsPath
    ]

    if threads == -1:
        args.extend(["--p-n-threads", "0"])
    elif threads is not None:
        args.extend(["--p-n-threads", str(threads)])

    command(args)


def metadataTabulate(inputFile: str, visualizationPath: str) -> None:
    command([
        "qiime", "metadata", "tabulate",
        "--m-input-file", inputFile,
        "--o-visualization", visualizationPath
    ])


def featureTableSummarize(inputPath: str, visualizationPath: str, metadataPath: str) -> None:
    command([
        "qiime", "feature-table", "summarize",
        "--i-table", inputPath,
        "--o-visualization", visualizationPath,
        "--m-sample-metadata-file", metadataPath
    ])


def featureTableTabulateSeqs(inputPath: str, visualizationPath: str) -> None:
    command([
        "qiime", "feature-table", "tabulate-seqs",
        "--i-data", inputPath,
        "--o-visualization", visualizationPath
    ])


def phylogenyAlignToTreeMafftFasttree(
    sequencesPath: str,
    aligmentPath: str,
    maskedAligmentPath: str,
    unrootedTreePath: str,
    rootedTreePath: str,
    threads: Optional[int] = -1
) -> None:

    args = [
        "qiime", "phylogeny", "align-to-tree-mafft-fasttree",
        "--i-sequences", sequencesPath,
        "--o-alignment", aligmentPath,
        "--o-masked-alignment", maskedAligmentPath,
        "--o-tree", unrootedTreePath,
        "--o-rooted-tree", rootedTreePath
    ]

    if threads == -1:
        args.extend(["--p-n-threads", "auto"])
    elif threads is not None:
        args.extend(["--p-n-threads", str(threads)])

    command(args)


def diversityCoreMetricsPhylogenetic(
    phlogenyPath: str,
    tablePath: str,
    samplingDepth: int,
    metadataPath: str,
    outputDir: str,
    threads: Optional[int] = -1
) -> None:

    args = [
        "qiime", "diversity", "core-metrics-phylogenetic",
        "--i-phylogeny", phlogenyPath,
        "--i-table", tablePath,
        "--p-sampling-depth", str(samplingDepth),
        "--m-metadata-file", metadataPath,
        "--output-dir", outputDir
    ]

    if threads == -1:
        args.extend(["--p-n-jobs-or-threads", "auto"])
    elif threads is not None:
        args.extend(["--p-n-jobs-or-threads", str(threads)])

    command(args)


def diversityAlphaGroupSignificance(
    alphaDiversityPath: str,
    metadataPath: str,
    visualizationPath: str
) -> None:

    command([
        "qiime", "diversity", "alpha-group-significance",
        "--i-alpha-diversity", alphaDiversityPath,
        "--m-metadata-file", metadataPath,
        "--o-visualization", visualizationPath
    ])


def diversityBetaGroupSignificance(
    distanceMatrixPath: str,
    metadataPath: str,
    metadataColumn: str,
    visualizationPath: str,
    pairwise: bool
) -> None:

    command([
        "qiime", "diversity", "beta-group-significance",
        "--i-distance-matrix", distanceMatrixPath,
        "--m-metadata-file", metadataPath,
        "--m-metadata-column", metadataColumn,
        "--o-visualization", visualizationPath,
        "--p-pairwise" if pairwise else ""
    ])


def emperorPlot(
    pcoaPath: str,
    metadataPath: str,
    customAxes: str,
    visualizationPath: str
) -> None:

    command([
        "qiime", "emperor", "plot",
        "--i-pcoa", pcoaPath,
        "--m-metadata-file", metadataPath,
        "--p-custom-axes", customAxes,
        "--o-visualization", visualizationPath
    ])


def diversityAlphaRarefaction(
    tablePath: str,
    phylogenyPath: str,
    maxDepth: int,
    metadataPath: str,
    visualizationPath: str
) -> None:

    command([
        "qiime", "diversity", "alpha-rarefaction",
        "--i-table", tablePath,
        "--i-phylogeny", phylogenyPath,
        "--p-max-depth", str(maxDepth),
        "--m-metadata-file", metadataPath,
        "--o-visualization", visualizationPath
    ])


def featureClassifierClassifySklearn(
    classifierPath: str,
    readsPath: str,
    classificationPath: str,
    threads: Optional[int] = -1
) -> None:

    args = [
        "qiime", "feature-classifier", "classify-sklearn",
        "--i-classifier", classifierPath,
        "--i-reads", readsPath,
        "--o-classification", classificationPath
    ]

    if threads == -1:
        args.extend(["--p-n-jobs", "-1"])
    elif threads is not None:
        args.extend(["--p-n-jobs", str(threads)])

    command(args)


def taxaBarplot(
    tablePath: str,
    taxonomyPath: str,
    metadataPath: str,
    visualizationPath: str
) -> None:

    command([
        "qiime", "taxa", "barplot",
        "--i-table", tablePath,
        "--i-taxonomy", taxonomyPath,
        "--m-metadata-file", metadataPath,
        "--o-visualization", visualizationPath
    ])


def featureTableFilterSamples(
    tablePath: str,
    metadataPath: str,
    where: str,
    filteredTablePath: str
) -> None:

    command([
        "qiime", "feature-table", "filter-samples",
        "--i-table", tablePath,
        "--m-metadata-file", metadataPath,
        "--p-where", where,
        "--o-filtered-table", filteredTablePath
    ])


def compositionAddPseudocount(tablePath: str, compositionTablePath: str) -> None:
    command([
        "qiime", "composition", "add-pseudocount",
        "--i-table", tablePath,
        "--o-composition-table", compositionTablePath
    ])


def compositionAncom(
    tablePath: str,
    metadataPath: str,
    metadataColumn: str,
    visualizationPath: str
) -> None:

    command([
        "qiime", "composition", "ancom",
        "--i-table", tablePath,
        "--m-metadata-file", metadataPath,
        "--m-metadata-column", metadataColumn,
        "--o-visualization", visualizationPath
    ])


def taxaCollapse(
    tablePath: str,
    taxonomyPath: str,
    level: int,
    collapsedTablePath: str
) -> None:

    command([
        "qiime", "taxa", "collapse",
        "--i-table", tablePath,
        "--i-taxonomy", taxonomyPath,
        "--p-level", str(level),
        "--o-collapsed-table", collapsedTablePath
    ])

def vsearchClusterDeNovo(
    tablePath: Union[str, Path],
    representativeSequencesPath: Union[str, Path],
    percIdentity: float,
    clusteredTablePath: Union[str, Path],
    clusteredSequencesPath: Union[str, Path],
    threads: Optional[int] = -1
) -> None:
    """
        Wrapper for QIIME2's vsearch de novo clusteing command.

        Parameters
        ----------
        tablePath : Union[str, Path]
            Path to the feature table generated by DADA2 denoise
        representativeSequencesPath : Union[str, Path]
            Path to the represenative sequences generated by DADA2 denoise
        percIdentity : float
            Percent identiy threshold for the OTU clustering
        clusteredTablePath : Union[str, Path]
            Path to the output clustered feature table
        clusteredSequencesPath : Union[str, Path]
            Path to the output clustered sequences
        multithreading : bool
            Number of threads to use for the process. If None, multithreading will not be used.
            Set to -1 (defaul) to use a thread for each CPU core
    """

    if isinstance(tablePath, Path):
        tablePath = str(tablePath)

    if isinstance(representativeSequencesPath, Path):
        representativeSequencesPath = str(representativeSequencesPath)

    if isinstance(clusteredTablePath, Path):
        clusteredTablePath = str(clusteredTablePath)

    if isinstance(clusteredSequencesPath, Path):
        clusteredSequencesPath = str(clusteredSequencesPath)

    args = [
        "qiime", "vsearch", "cluster-features-de-novo",
        "--i-table", tablePath,
        "--i-sequences", representativeSequencesPath,
        "--p-perc-identity", str(percIdentity),
        "--o-clustered-table", clusteredTablePath,
        "--o-clustered-sequences", clusteredSequencesPath
    ]

    if threads == -1:
        args.extend(["--p-threads", "0"])
    elif threads is not None:
        args.extend(["--p-threads", str(threads)])

    command(args)


def vsearchClusterClosedReference(
    tablePath: Union[str, Path],
    representativeSequencesPath: Union[str, Path],
    referenceSequencesPath: Union[str, Path],
    percIdentity: float,
    clusteredTablePath: Union[str, Path],
    clusteredSequencesPath: Union[str, Path],
    unmatchedSequencesPath: Union[str, Path],
    threads: Optional[int] = -1
) -> None:
    """
        Wrapper for QIIME2's vsearch closed reference clusteing command.

        Parameters
        ----------
        tablePath : Union[str, Path]
            Path to the feature table generated by DADA2 denoise
        representativeSequencesPath : Union[str, Path]
            Path to the represenative sequences generated by DADA2 denoise
        referenceSequencesPath : Union[str, Path]
            Path to reference OTU sequences
        percIdentity : float
            Percent identiy threshold for the OTU clustering
        clusteredTablePath : Union[str, Path]
            Path to the output clustered feature table
        clusteredSequencesPath : Union[str, Path]
            Path to the output clustered sequences
        unmatchedSequencesPath : Union[str, Path]
            Path to the output unmatched sequences
        multithreading : bool
            Number of threads to use for the process. If None, multithreading will not be used.
            Set to -1 (defaul) to use a thread for each CPU core
    """

    if isinstance(tablePath, Path):
        tablePath = str(tablePath)

    if isinstance(representativeSequencesPath, Path):
        representativeSequencesPath = str(representativeSequencesPath)

    if isinstance(referenceSequencesPath, Path):
        referenceSequencesPath = str(referenceSequencesPath)

    if isinstance(clusteredTablePath, Path):
        clusteredTablePath = str(clusteredTablePath)

    if isinstance(clusteredSequencesPath, Path):
        clusteredSequencesPath = str(clusteredSequencesPath)

    if isinstance(unmatchedSequencesPath, Path):
        unmatchedSequencesPath = str(unmatchedSequencesPath)

    args = [
        "qiime", "vsearch", "cluster-features-closed-reference",
        "--i-table", tablePath,
        "--i-sequences", representativeSequencesPath,
        "--i-reference-sequences", referenceSequencesPath,
        "--p-perc-identity", str(percIdentity),
        "--o-clustered-table", clusteredTablePath,
        "--o-clustered-sequences", clusteredSequencesPath,
        "--o-unmatched-sequences", unmatchedSequencesPath
    ]

    if threads == -1:
        args.extend(["--p-threads", "0"])
    elif threads is not None:
        args.extend(["--p-threads", str(threads)])

    command(args)


def vsearchClusterOpenReference(
    tablePath: Union[str, Path],
    representativeSequencesPath: Union[str, Path],
    referenceSequencesPath: Union[str, Path],
    percIdentity: float,
    clusteredTablePath: Union[str, Path],
    clusteredSequencesPath: Union[str, Path],
    newReferenceSequencesPath: Union[str, Path],
    threads: Optional[int] = -1
) -> None:
    """
        Wrapper for QIIME2's vsearch open reference clusteing command.

        Parameters
        ----------
        tablePath : Union[str, Path]
            Path to the feature table generated by DADA2 denoise
        representativeSequencesPath : Union[str, Path]
            Path to the represenative sequences generated by DADA2 denoise
        referenceSequencesPath : Union[str, Path]
            Path to reference OTU sequences
        percIdentity : float
            Percent identiy threshold for the OTU clustering
        clusteredTablePath : Union[str, Path]
            Path to the output clustered feature table
        clusteredSequencesPath : Union[str, Path]
            Path to the output clustered sequences
        newReferenceSequencesPath : Union[str, Path]
            Path to the output new reference sequences
        multithreading : bool
            Number of threads to use for the process. If None, multithreading will not be used.
            Set to -1 (defaul) to use a thread for each CPU core
    """

    if isinstance(tablePath, Path):
        tablePath = str(tablePath)

    if isinstance(representativeSequencesPath, Path):
        representativeSequencesPath = str(representativeSequencesPath)

    if isinstance(referenceSequencesPath, Path):
        referenceSequencesPath = str(referenceSequencesPath)

    if isinstance(clusteredTablePath, Path):
        clusteredTablePath = str(clusteredTablePath)

    if isinstance(clusteredSequencesPath, Path):
        clusteredSequencesPath = str(clusteredSequencesPath)

    if isinstance(newReferenceSequencesPath, Path):
        newReferenceSequencesPath = str(newReferenceSequencesPath)

    args = [
        "qiime", "vsearch", "cluster-features-open-reference",
        "--i-table", tablePath,
        "--i-sequences", representativeSequencesPath,
        "--i-reference-sequences", referenceSequencesPath,
        "--p-perc-identity", str(percIdentity),
        "--o-clustered-table", clusteredTablePath,
        "--o-clustered-sequences", clusteredSequencesPath,
        "--o-new-reference-sequences", newReferenceSequencesPath
    ]

    if threads == -1:
        args.extend(["--p-threads", "0"])
    elif threads is not None:
        args.extend(["--p-threads", str(threads)])

    command(args)
